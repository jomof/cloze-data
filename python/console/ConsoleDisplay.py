import inspect
import os
import queue
import sys
import threading
import time
import traceback  # Keep for now, though error messages are also event-driven

class ConsoleDisplay:
    """
    Handles interactive console display for operations, progress, and statistics.

    The caller should use begin(), finish(), and error() to report work items with a type tag.
    ConsoleDisplay maintains a list of items and shows active or recently finished ones,
    and summarizes how many of each type are active, as well as total accumulated time per type.
    """
    CLEAR_TO_EOL    = "\u001b[K"
    MOVE_UP         = staticmethod(lambda n: f"\u001b[{n}A")
    MOVE_DOWN       = staticmethod(lambda n: f"\u001b[{n}B")
    HIDE_CURSOR     = "\u001b[?25l"
    SHOW_CURSOR     = "\u001b[?25h"
    SAVE_CURSOR     = "\u001b[s"
    RESTORE_CURSOR  = "\u001b[u"
    CLEAR_DOWN      = "\u001b[J"
    SAVE_STATE      = "\u001b7"
    RESTORE_STATE   = "\u001b8"
    FOREGROUND_GREEN = "\u001b[32m"

    DEFAULT_REFRESH_INTERVAL = 0.2
    SCAVENGING_INTERVAL      = 2.0   # seconds, how often to remove old items
    SCAVENGING_AGE_LIMIT     = 2.0  # seconds, remove finished/error items older than this

    def __init__(self, window_size: int = 5, refresh_interval: float = None):
        self.window_size     = window_size
        self.refresh_interval = refresh_interval or self.DEFAULT_REFRESH_INTERVAL

        # Track global start time for total wall clock
        self.start_time = None

        # event_queue holds dicts: {'type': 'BEGIN'|'FINISH'|'ERROR'|'COUNTDOWN_UPDATE',
        #                          'slot_key': str, 'text': str, 'item_type': str, 'time': float,
        #                          'value': int (for COUNTDOWN_UPDATE)}
        self.event_queue = queue.Queue()
        # items maps slot_key to { 'text': str, 'time': float (start or finish), 'status': 'active'|'complete'|'error', 'item_type': str }
        self.items = {}
        # Track the order in which item_types first appear
        self.type_order = []
        # Countdown if needed by caller
        self.countdown = 0

        # Summary counts and times of completed/error items by type
        self.summary_counts = {}  # e.g. { 'Reading': 3, 'Mapping': 5, … }
        self.summary_times  = {}  # e.g. { 'Reading': 12.7, 'Mapping': 5.3, … }

        self.watcher_thread      = None
        self.watch_done_event    = threading.Event()
        self.last_scavenge_time  = time.monotonic()
        self.final_summary_lines = []
        self.final_message = None
        self._in_error_handling = False
        self._is_stopping = False  # Track if we're in shutdown mode
        
    def _scavenge_items(self):
        """Remove finished/error items older than SCAVENGING_AGE_LIMIT."""
        now = time.monotonic()
        to_remove = []
        
        # First pass: identify items to remove (snapshot the dict to avoid modification during iteration)
        items_snapshot = dict(self.items)
        for key, v in items_snapshot.items():
            if v['status'] in ['complete', 'error'] and (now - v['time']) > self.SCAVENGING_AGE_LIMIT:
                to_remove.append(key)
        
        # Second pass: safely remove items
        for key in to_remove:
            # Use pop() instead of del to avoid KeyError if key was already removed
            removed_item = self.items.pop(key, None)
            if removed_item is None:
                # Item was already removed, this is fine - just don't warn about it
                pass

    def _apply_event(self, event: dict):
        ev_type   = event.get('type')
        slot_key  = event.get('slot_key')
        text      = event.get('text', '')
        ts        = event.get('time', time.monotonic())
        item_type = event.get('item_type', 'Unknown')

        # Handle countdown updates separately
        if ev_type == 'COUNTDOWN_UPDATE':
            self.countdown = event.get('value', self.countdown)
            return

        # Only process BEGIN, FINISH, ERROR
        if ev_type not in ['BEGIN', 'FINISH', 'ERROR']:
            return

        # BEGIN event: record a new active item
        if ev_type == 'BEGIN':
            # Track new types in order
            if item_type not in self.type_order:
                self.type_order.append(item_type)
            # Create or update item as active, store start time
            self.items[slot_key] = {
                'text': text,
                'time': ts,
                'status': 'active',
                'item_type': item_type
            }
            return

        # FINISH or ERROR: update existing or create
        # Determine the previous entry for this slot_key
        prev_entry = self.items.get(slot_key, {})
        prev_type  = prev_entry.get('item_type', item_type)
        start_ts   = prev_entry.get('time', ts)   # fallback to ts if missing
        elapsed    = ts - start_ts

        # Accumulate elapsed time for that type
        self.summary_times[prev_type] = self.summary_times.get(prev_type, 0.0) + elapsed

        # Update summary counts
        status = 'complete' if ev_type == 'FINISH' else 'error'
        self.summary_counts[prev_type] = self.summary_counts.get(prev_type, 0) + 1

        # Overwrite or update the item so the display can show final text
        self.items[slot_key] = {
            'text': text,
            'time': ts,
            'status': status,
            'item_type': prev_type
        }

    def _drain_all_events(self):
        """Drain all queued events except 'DONE'."""
        while True:
            try:
                extra = self.event_queue.get_nowait()
            except queue.Empty:
                break

            if isinstance(extra, dict):
                self._apply_event(extra)
            elif isinstance(extra, str) and extra == 'DONE':
                # Put 'DONE' back and stop draining
                self.event_queue.put('DONE')
                return

    def _do_redraw(self):
        """
        Redraw the console window: 
        - Show up to `window_size` lines of active/finished items (newest first).
        - Then show per-type counts of currently active items.
        - Finally show countdown if set.
        """
        # Don't redraw if we're stopping
        if self._is_stopping:
            return
            
        lines       = [self.SAVE_CURSOR]
        clear_to_eol = self.CLEAR_TO_EOL
        now         = time.monotonic()

        # Build lists: active items (newest first), finished items (newest first)
        active_items   = []
        finished_items = []
        type_counts    = {t: 0 for t in self.type_order}
        items_snapshot = dict(self.items)

        for v in items_snapshot.values():
            display_text = v['text']
            status       = v['status']
            msg_time     = v['time']
            item_type    = v.get('item_type', 'Unknown')

            if status == 'active':
                # count active types
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
                elapsed = now - msg_time
                line = f"  {display_text}"
                if elapsed > 1.0:
                    line += f" ({elapsed:.1f}s)"
                line += clear_to_eol + "\n"
                active_items.append((msg_time, line))
            else:
                line = f"  {display_text}"
                line += clear_to_eol + "\n"
                finished_items.append((msg_time, line))

        # Sort by time descending (newest first)
        active_items.sort(key=lambda x: x[0], reverse=True)
        finished_items.sort(key=lambda x: x[0], reverse=True)

        # Select up to window_size: prioritize active, then finished
        final_lines = []
        slots = self.window_size

        for _, line in active_items[:slots]:
            final_lines.append(line)
        slots -= len(final_lines)

        if slots > 0:
            for _, line in finished_items[:slots]:
                final_lines.append(line)
            slots -= len(finished_items[:slots])

        # If fewer than window_size, pad with blank lines
        for _ in range(max(0, self.window_size - len(final_lines))):
            final_lines.append(f"  {clear_to_eol}\n")

        # Display items first
        lines.extend(final_lines)

        # Display summary of active counts by type, in order of first arrival
        for t in self.type_order:
            count = type_counts.get(t, 0)
            lines.append(f"{t}: {count} active{clear_to_eol}\n")

        # Display countdown if set
        lines.append(f"{self.countdown} work items remaining{clear_to_eol}\n")

        # Final message if set
        if self.final_message:
            lines.append(f"{self.final_message}{clear_to_eol}\n")

        lines.append(self.CLEAR_DOWN)  # Clear below cursor

        lines.append(self.RESTORE_CURSOR)
        try:
            sys.stdout.write('\r')
            sys.stdout.write(''.join(lines))
            sys.stdout.flush()
        except (ValueError, OSError):
            # Output stream might be closed during shutdown, ignore
            pass

    def _watcher_loop(self):
        """
        Thread loop that:
        - Periodically scavenges old items.
        - Processes incoming events (BEGIN, FINISH, ERROR, COUNTDOWN_UPDATE).
        - Redraws at least every refresh_interval seconds.
        - When receiving 'DONE', drains remaining events, does a final redraw, and prints summary.
        """
        refresh_interval = self.refresh_interval
        half_interval    = refresh_interval / 2.0
        last_redraw      = time.monotonic() - refresh_interval

        while True:
            now = time.monotonic()

            # Periodically scavenge old finished/error items
            if not self._is_stopping and now - self.last_scavenge_time >= self.SCAVENGING_INTERVAL:
                self._scavenge_items()
                self.last_scavenge_time = now

            try:
                event = self.event_queue.get(timeout=half_interval)
            except queue.Empty:
                # If no event, maybe redraw if it's time
                if not self._is_stopping and now - last_redraw >= refresh_interval:
                    self._do_redraw()
                    last_redraw = now
                continue

            # If 'DONE' sentinel, break out after final summary
            if isinstance(event, str) and event == 'DONE':
                self._is_stopping = True
                # Drain remaining events (except DONE)
                self._drain_all_events()
                # Final redraw of active/finished window
                self._do_redraw()
                # Clear below cursor for summary
                try:
                    sys.stdout.write(self.CLEAR_DOWN)
                    sys.stdout.write(f'\r{self.CLEAR_TO_EOL}')

                    # Print formatted per-type summary
                    for t in self.type_order:
                        count = self.summary_counts.get(t, 0)
                        total = self.summary_times.get(t, 0.0)
                        type_label = f'{t}:'
                        sys.stdout.write(f"{type_label:<20} {count} items, {total:.1f}s\n")

                    # Print total wall clock time
                    total_wall_time = now - self.start_time if self.start_time is not None else 0.0
                    sys.stdout.write(f"{'Total time:':<20} {total_wall_time:.1f}s\n")

                    # Any additional final_summary_lines
                    for line in self.final_summary_lines:
                        sys.stdout.write(line)
                    sys.stdout.flush()
                except (ValueError, OSError):
                    # Output stream might be closed, ignore
                    pass
                self.watch_done_event.set()
                break

            # Otherwise, it's a dict event: apply it and drain any others
            if isinstance(event, dict):
                self._apply_event(event)
                self._drain_all_events()

            # Possibly redraw if enough time has elapsed
            if not self._is_stopping and now - last_redraw >= refresh_interval:
                self._do_redraw()
                last_redraw = now

    def start(self):
        """Begin the watcher thread and hide the cursor."""
        # Record the start time when watcher begins
        self.start_time = time.monotonic()
        self._is_stopping = False
        try:
            sys.stdout.write(self.HIDE_CURSOR)
            sys.stdout.flush()
        except (ValueError, OSError):
            # Output stream might be closed, ignore
            pass
        self.watch_done_event.clear()
        self.watcher_thread = threading.Thread(target=self._watcher_loop, daemon=True)
        self.watcher_thread.start()

    def stop(self):
        """
        Signal the watcher thread to finish by enqueuing 'DONE', then wait for it.
        Finally, restore the cursor.
        """
        self._is_stopping = True
        if self.watcher_thread and self.watcher_thread.is_alive():
            self.event_queue.put('DONE')
            # Wait up to a short timeout for the watcher to clean up
            self.watch_done_event.wait(timeout=max(self.refresh_interval * 2, 1.0))
        try:
            sys.stdout.write(self.SHOW_CURSOR)
            sys.stdout.flush()
        except (ValueError, OSError):
            # Output stream might be closed, ignore
            pass

    def _caller_file_line(self, n):
        try:
            stack = inspect.stack()
            # [0] is this frame, [1] is _debug_print_caller_message caller, [2] is the original caller
            caller_frame_info = stack[n+1]
            filename = os.path.basename(caller_frame_info.filename)
            lineno   = caller_frame_info.lineno
            return f"{filename}:{lineno}"
        except (IndexError, AttributeError):
            return "unknown:0"

    def _debug_print_caller_message(self, message: str):
        """
        Print a debug message including the filename and line number of the caller.
        Only exit if we're not in shutdown mode.
        """
        if self._is_stopping:
            # During shutdown, just print the message without stack trace or exit
            try:
                sys.stdout.write(f"\n❌ {message}\n")
                sys.stdout.flush()
            except (ValueError, OSError):
                pass
            return
            
        caller = self._caller_file_line(2)
        try:
            print(f"\n❌ {caller}: {message}\n")
            traceback.print_stack()
            sys.stdout.flush()
        except (ValueError, OSError):
            pass
        sys.exit(1)

    class MessageScope:
        def __init__(self, display, slot_key: str, message: str, item_type: str):
            self.display = display
            self.slot_key = slot_key
            self.message = message
            self.item_type = item_type
        
        def __enter__(self):
            if not self.display._is_stopping:
                self.display._begin(self.slot_key, self.message, self.item_type)
            return self
        
        def __exit__(self, exc_type, exc_value, tb):
            if self.display._is_stopping:
                # During shutdown, don't report errors or completions
                return False
                
            if exc_type is not None:
                traceback.print_exception(exc_type, exc_value, tb)
                # self.display._error(self.slot_key, f"exception while {self.message}", caller_level=2)
            else:
                self.display._finish(self.slot_key, f"finished {self.message}")
            return False #Propagate exceptions

    def work(self, slot_key: str, item_type: str):
        return self.MessageScope(self, f"{item_type}:{slot_key}", f"{item_type} {slot_key}", item_type)

    def _begin(self, slot_key: str, message: str, item_type: str):
        """Mark a work item as started with a given type."""
        if self._is_stopping:
            return
        self.event_queue.put({
            'type': 'BEGIN',
            'slot_key': slot_key,
            'text': f'🔄 {message}',
            'item_type': item_type,
            'time': time.monotonic()
        })

    def _finish(self, slot_key: str, message: str):
        """Mark a work item as completed."""
        if self._is_stopping:
            return
        self.event_queue.put({
            'type': 'FINISH',
            'slot_key': slot_key,
            'text': f'✅ {message}',
            # No need to pass item_type here; _apply_event will read existing type
            'time': time.monotonic()
        })

    def _error(self, slot_key: str, message: str, caller_level: int = 1):
        if self._in_error_handling or self._is_stopping:
            # Prevent recursion or errors during shutdown: just write to stdout and return
            try:
                sys.stdout.write(f'❌ {message}\n')
                sys.stdout.flush()
            except (ValueError, OSError):
                pass
            return
            
        self._in_error_handling = True
        try:     
            self._debug_print_caller_message(f"\n❌ {message}")
            self.event_queue.put({
                'type': 'ERROR',
                'slot_key': slot_key,
                'text': f'❌ {message}',
                'time': time.monotonic()
            })
        finally:
            self._in_error_handling = False
        

    def error(self, message: str):
        self._error('GENERAL_ERROR', message)

    def warn(self, message: str):
        """Print a warning immediately (not tied to any slot)."""
        if not self._is_stopping:
            try:
                sys.stdout.write(f'\r⚠️  {message} {self.CLEAR_TO_EOL}\n')
                sys.stdout.flush()
            except (ValueError, OSError):
                pass

    def info(self, message: str, slot_key: str = None):
        if not self._is_stopping:
            try:
                sys.stdout.write(f'\rℹ️ {message} {self.CLEAR_TO_EOL}\n')
                sys.stdout.flush()
            except (ValueError, OSError):
                pass

    def check(self, message: str):
        if not self._is_stopping:
            try:
                sys.stdout.write(f'\r🌟 {message} {self.CLEAR_TO_EOL}\n')
                sys.stdout.flush()
            except (ValueError, OSError):
                pass

    def update_countdown(self, count: int):
        """Update the countdown of remaining work items."""
        if not self._is_stopping:
            self.event_queue.put({
                'type': 'COUNTDOWN_UPDATE',
                'value': count,
                'time': time.monotonic()
            })

    def warn_canceling(self, message: str):
        """Cancel the current run, if any."""
        self._is_stopping = True
        try:
            sys.stdout.write("\r")
            sys.stdout.write(self.SAVE_CURSOR)
            sys.stdout.write(self.CLEAR_DOWN)
            sys.stdout.write(self.RESTORE_CURSOR)
            sys.stdout.flush()
        except (ValueError, OSError):
            pass
        self.final_message = f"⚠️ {message}"
        self.event_queue.put('DONE')
        self.watch_done_event.wait(timeout=max(self.refresh_interval * 2, 1.0))

# Global instance
_display_instance = ConsoleDisplay()

# Export the instance
display = _display_instance