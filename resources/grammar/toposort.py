import os
from grammar_summary import generate_summary, save_summary
import yaml
from collections import defaultdict, deque
import asyncio
from python.mapreduce import MapReduce
from python.console import display
import logging
import json
from python.grammar import clean_lint_memoize

from collections import defaultdict, deque
from typing import List, Dict, Set, Tuple, Any, Optional

tlogging = logging.getLogger(__name__)
from collections import defaultdict, deque
from typing import List, Dict, Set, Tuple, Any, Optional

def update_priority_list_minimal(
    current_list: List[str],
    nodes_dict: Dict[str, Dict[str, List[str]]],
    before_field: str = "before",
    after_field: str = "after",
    max_edits: Optional[int] = None,
    insert_missing_strategy: str = "best_position",
    ensure_all_missing_added: bool = True
) -> Tuple[List[str], List[str]]:
    """
    Update a priority list with minimal changes, respecting existing order as much as possible.
    
    Args:
        current_list: Existing list in priority order (may be incomplete)
        nodes_dict: Dict mapping node names to constraint info
        before_field: Field name for items that should come before this node
        after_field: Field name for items that should come after this node
        max_edits: Maximum number of edits to make (None for unlimited)
        insert_missing_strategy: How to insert missing items ("end", "best_position", "constraint_based")
        ensure_all_missing_added: If True, always add all missing items (doesn't count toward max_edits)
    
    Returns:
        Tuple of (updated_list, list_of_changes_made)
    """
    
    result = current_list.copy()
    changes = []
    edits_made = 0
    
    # First, remove items that don't exist in nodes_dict
    all_nodes = set(nodes_dict.keys())
    items_to_remove = [item for item in result if item not in all_nodes]
    
    for item in items_to_remove:
        result.remove(item)
        changes.append(f"Removed '{item}' (not in nodes_dict)")
        # Note: removing items doesn't count toward max_edits since it's cleanup
    
    # Then, add missing items
    missing_nodes = all_nodes - set(result)  # Use result (after removals) instead of current_list
    
    if missing_nodes:
        for node in missing_nodes:
            # If ensure_all_missing_added is True, always add missing items
            # Otherwise, respect max_edits limit
            if not ensure_all_missing_added and max_edits and edits_made >= max_edits:
                break
                
            best_pos = find_best_insertion_position(
                result, node, nodes_dict, before_field, after_field, insert_missing_strategy
            )
            result.insert(best_pos, node)
            changes.append(f"Added '{node}' at position {best_pos}")
            
            # Only count toward edits if we're not ensuring all missing are added
            if not ensure_all_missing_added:
                edits_made += 1
    
    # Then, fix constraint violations with minimal moves
    if not max_edits or edits_made < max_edits:
        violations = find_constraint_violations(result, nodes_dict, before_field, after_field)
        
        # Sort violations by importance score (highest first)
        violation_scores = []
        for violation in violations:
            score = score_violation_importance(violation, result, nodes_dict, before_field, after_field)
            violation_scores.append((score, violation))
        
        violation_scores.sort(key=lambda x: x[0], reverse=True)
        
        for score, violation in violation_scores:
            if max_edits and edits_made >= max_edits:
                break
                
            if fix_violation_minimal(result, violation, changes):
                edits_made += 1
    
    return result, changes


def find_best_insertion_position(
    current_list: List[str],
    node: str,
    nodes_dict: Dict[str, Dict[str, List[str]]],
    before_field: str,
    after_field: str,
    strategy: str
) -> int:
    """Find the best position to insert a missing node."""
    
    if strategy == "end":
        return len(current_list)
    
    constraints = nodes_dict.get(node, {})
    before_items = set(constraints.get(before_field, []))
    after_items = set(constraints.get(after_field, []))
    
    # Find constraints that exist in current list
    before_positions = [i for i, item in enumerate(current_list) if item in before_items]
    after_positions = [i for i, item in enumerate(current_list) if item in after_items]
    
    if strategy == "constraint_based":
        # Insert after the latest "before" item and before the earliest "after" item
        min_pos = max(before_positions) + 1 if before_positions else 0
        max_pos = min(after_positions) if after_positions else len(current_list)
        return min(min_pos, max_pos)
    
    else:  # "best_position"
        # Score each position based on how many constraints it satisfies
        best_pos = 0
        best_score = -1
        
        for pos in range(len(current_list) + 1):
            score = 0
            
            # Check how many before/after constraints this position satisfies
            for i, item in enumerate(current_list):
                if item in before_items and i < pos:
                    score += 1
                elif item in after_items and i >= pos:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_pos = pos
        
        return best_pos


def find_constraint_violations(
    current_list: List[str],
    nodes_dict: Dict[str, Dict[str, List[str]]],
    before_field: str,
    after_field: str
) -> List[Dict]:
    """Find all constraint violations in the current list."""
    
    violations = []
    positions = {item: i for i, item in enumerate(current_list)}
    
    for node, constraints in nodes_dict.items():
        if node not in positions:
            continue
            
        node_pos = positions[node]
        
        # Check "before" constraints
        for before_item in constraints.get(before_field, []):
            if before_item in positions and positions[before_item] > node_pos:
                violations.append({
                    'type': 'before',
                    'node': node,
                    'violating_item': before_item,
                    'node_pos': node_pos,
                    'violating_pos': positions[before_item],
                    'distance': positions[before_item] - node_pos
                })
        
        # Check "after" constraints
        for after_item in constraints.get(after_field, []):
            if after_item in positions and positions[after_item] < node_pos:
                violations.append({
                    'type': 'after',
                    'node': node,
                    'violating_item': after_item,
                    'node_pos': node_pos,
                    'violating_pos': positions[after_item],
                    'distance': node_pos - positions[after_item]
                })
    
    return violations


def score_violation_importance(
    violation: Dict,
    current_list: List[str],
    nodes_dict: Dict,
    before_field: str,
    after_field: str
) -> float:
    """Score a violation's importance (higher = more important to fix)."""
    
    score = 0.0
    node = violation['node']
    violating_item = violation['violating_item']
    
    # Weight 1: Items with more constraints are more important
    node_constraint_count = len(nodes_dict.get(node, {}).get(before_field, [])) + len(nodes_dict.get(node, {}).get(after_field, []))
    violating_constraint_count = len(nodes_dict.get(violating_item, {}).get(before_field, [])) + len(nodes_dict.get(violating_item, {}).get(after_field, []))
    score += (node_constraint_count + violating_constraint_count) * 2
    
    # Weight 2: Cascade impact
    cascade_impact = calculate_cascade_impact(violation, current_list, nodes_dict, before_field, after_field)
    score += cascade_impact * 5
    
    # Weight 3: Distance penalty (smaller distances are easier fixes, but don't over-prioritize)
    distance_penalty = 1.0 / (1.0 + violation['distance'])
    score += distance_penalty
    
    # Weight 4: Position in list (slight preference for fixing items that appear earlier)
    position_weight = (len(current_list) - min(violation['node_pos'], violation['violating_pos'])) / len(current_list)
    score += position_weight * 0.5
    
    return score


def calculate_cascade_impact(
    violation: Dict, 
    current_list: List[str], 
    nodes_dict: Dict, 
    before_field: str, 
    after_field: str
) -> int:
    """Calculate how many other violations fixing this one might resolve."""
    
    node = violation['node']
    violating_item = violation['violating_item']
    
    # Simulate the fix and count how many violations it would resolve
    temp_list = current_list.copy()
    
    try:
        node_idx = temp_list.index(node)
        violating_idx = temp_list.index(violating_item)
        
        if violation['type'] == 'before':
            item = temp_list.pop(violating_idx)
            new_pos = node_idx if violating_idx > node_idx else node_idx - 1
            temp_list.insert(new_pos, item)
        else:
            item = temp_list.pop(violating_idx)
            new_pos = node_idx + 1 if violating_idx < node_idx else node_idx
            temp_list.insert(new_pos, item)
        
        # Count violations before and after
        original_violations = len(find_constraint_violations(current_list, nodes_dict, before_field, after_field))
        new_violations = len(find_constraint_violations(temp_list, nodes_dict, before_field, after_field))
        
        return original_violations - new_violations  # Positive if we fixed more than we broke
        
    except (ValueError, IndexError):
        return 0


def fix_violation_minimal(result: List[str], violation: Dict, changes: List[str]) -> bool:
    """Fix a single violation with minimal change."""
    
    node = violation['node']
    violating_item = violation['violating_item']
    
    # Find current positions
    try:
        node_idx = result.index(node)
        violating_idx = result.index(violating_item)
    except ValueError:
        return False  # Items no longer in list
    
    if violation['type'] == 'before':
        # Move violating_item to just before node
        item = result.pop(violating_idx)
        new_pos = node_idx if violating_idx > node_idx else node_idx - 1
        result.insert(new_pos, item)
        changes.append(f"Moved '{violating_item}' before '{node}' (position {violating_idx} -> {new_pos})")
        
    else:  # 'after'
        # Move violating_item to just after node
        item = result.pop(violating_idx)
        new_pos = node_idx + 1 if violating_idx < node_idx else node_idx
        result.insert(new_pos, item)
        changes.append(f"Moved '{violating_item}' after '{node}' (position {violating_idx} -> {new_pos})")
    
    return True


def analyze_constraints(
    current_list: List[str],
    nodes_dict: Dict[str, Dict[str, List[str]]],
    before_field: str = "before",
    after_field: str = "after"
) -> Dict:
    """Analyze the current list and show what changes would be made."""
    
    violations = find_constraint_violations(current_list, nodes_dict, before_field, after_field)
    all_nodes = set(nodes_dict.keys())
    missing = all_nodes - set(current_list)
    invalid = set(current_list) - all_nodes
    
    return {
        'violations': len(violations),
        'missing_items': len(missing),
        'invalid_items': len(invalid),
        'violation_details': violations,
        'missing_items_list': list(missing),
        'invalid_items_list': list(invalid)
    }


def update_priority_list(
    current_list: List[str],
    nodes_dict: Dict[str, Dict[str, List[str]]],
    before_field: str = "before",
    after_field: str = "after",
    max_edits: Optional[int] = None,
    ensure_all_missing_added: bool = True
) -> List[str]:
    """Original function signature for backwards compatibility."""
    result, _ = update_priority_list_minimal(
        current_list, nodes_dict, before_field, after_field, max_edits, 
        ensure_all_missing_added=ensure_all_missing_added
    )
    return result


def find_minimal_constraint_cuts(
    current_list: List[str],
    nodes_dict: Dict[str, Dict[str, List[str]]],
    before_field: str = "before",
    after_field: str = "after",
    cut_all_backward_edges: bool = True
) -> Tuple[List[Tuple[str, str, str]], Dict[str, Dict[str, List[str]]]]:
    """
    Find constraint edges to remove to make the DAG respect the current ordering.
    
    Args:
        current_list: The desired order
        nodes_dict: Original constraint data
        before_field: Field name for items that should come before this node
        after_field: Field name for items that should come after this node
        cut_all_backward_edges: If True, cuts ALL edges that go backward in the ordering,
                               even if they don't create violations (prevents future cycles)
    
    Returns:
        Tuple of (list_of_cuts, updated_nodes_dict)
        where cuts are (from_node, to_node, constraint_type) tuples
    """
    
    # Create position mapping
    positions = {item: i for i, item in enumerate(current_list)}
    
    # Find all edges that go backward in our ordering
    cuts_needed = []
    
    for node, constraints in nodes_dict.items():
        if node not in positions:
            continue
            
        node_pos = positions[node]
        
        # Check "before" constraints - these create edges FROM before_item TO node
        for before_item in constraints.get(before_field, []):
            if before_item in positions:
                before_pos = positions[before_item]
                # If before_item comes after node in our ordering, this edge goes backward
                if cut_all_backward_edges and before_pos > node_pos:
                    cuts_needed.append((before_item, node, f"{node}.{before_field}", before_item))
                elif not cut_all_backward_edges and before_pos > node_pos:
                    # Only cut if it creates a violation (original behavior)
                    cuts_needed.append((before_item, node, f"{node}.{before_field}", before_item))
        
        # Check "after" constraints - these create edges FROM node TO after_item  
        for after_item in constraints.get(after_field, []):
            if after_item in positions:
                after_pos = positions[after_item]
                # If after_item comes before node in our ordering, this edge goes backward
                if cut_all_backward_edges and after_pos < node_pos:
                    cuts_needed.append((node, after_item, f"{node}.{after_field}", after_item))
                elif not cut_all_backward_edges and after_pos < node_pos:
                    # Only cut if it creates a violation (original behavior)  
                    cuts_needed.append((node, after_item, f"{node}.{after_field}", after_item))
    
    # Create updated nodes_dict with cuts applied
    updated_nodes_dict = {}
    for node, constraints in nodes_dict.items():
        updated_constraints = {}
        
        # Copy before constraints, removing cut ones
        if before_field in constraints:
            updated_before = []
            for before_item in constraints[before_field]:
                # Keep this constraint unless it's in our cuts
                should_cut = any(cut[0] == before_item and cut[1] == node and cut[3] == before_item
                               for cut in cuts_needed)
                if not should_cut:
                    updated_before.append(before_item)
            updated_constraints[before_field] = updated_before
        
        # Copy after constraints, removing cut ones  
        if after_field in constraints:
            updated_after = []
            for after_item in constraints[after_field]:
                # Keep this constraint unless it's in our cuts
                should_cut = any(cut[0] == node and cut[1] == after_item and cut[3] == after_item
                               for cut in cuts_needed)
                if not should_cut:
                    updated_after.append(after_item)
            updated_constraints[after_field] = updated_after
        
        # Copy any other fields unchanged
        for field, value in constraints.items():
            if field not in [before_field, after_field]:
                updated_constraints[field] = value
                
        updated_nodes_dict[node] = updated_constraints
    
    # Remove the extra field from cuts_needed for return
    cuts_cleaned = [(cut[0], cut[1], cut[2]) for cut in cuts_needed]
    
    return cuts_cleaned, updated_nodes_dict


def find_cycles_in_dag(
    nodes_dict: Dict[str, Dict[str, List[str]]],
    before_field: str = "before",
    after_field: str = "after"
) -> List[List[str]]:
    """
    Find all cycles in the constraint graph.
    """
    
    # Build the graph
    graph = defaultdict(set)
    all_nodes = set(nodes_dict.keys())
    
    for node, constraints in nodes_dict.items():
        # Items in 'before' should come before this node
        for before_item in constraints.get(before_field, []):
            if before_item in all_nodes:
                graph[before_item].add(node)
        
        # This node should come before items in 'after'
        for after_item in constraints.get(after_field, []):
            if after_item in all_nodes:
                graph[node].add(after_item)
    
    # Find strongly connected components (cycles)
    def tarjan_scc():
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        sccs = []
        
        def strongconnect(node):
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True
            
            for successor in graph.get(node, set()):
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif on_stack.get(successor, False):
                    lowlinks[node] = min(lowlinks[node], index[successor])
            
            if lowlinks[node] == index[node]:
                component = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    component.append(w)
                    if w == node:
                        break
                sccs.append(component)
        
        for node in all_nodes:
            if node not in index:
                strongconnect(node)
        
        return sccs
    
    # Return only cycles (SCCs with more than 1 node)
    sccs = tarjan_scc()
    cycles = [scc for scc in sccs if len(scc) > 1]
    
    return cycles


def analyze_dag_with_cuts(
    current_list: List[str],
    nodes_dict: Dict[str, Dict[str, List[str]]],
    before_field: str = "before", 
    after_field: str = "after",
    cut_all_backward_edges: bool = True
) -> Dict:
    """
    Analyze what cuts would be needed and verify the result.
    """
    
    # Find cycles in original DAG
    original_cycles = find_cycles_in_dag(nodes_dict, before_field, after_field)
    
    # Get original violations
    original_violations = find_constraint_violations(current_list, nodes_dict, before_field, after_field)
    
    # Find cuts needed
    cuts, updated_nodes_dict = find_minimal_constraint_cuts(
        current_list, nodes_dict, before_field, after_field, cut_all_backward_edges
    )
    
    # Check cycles after cuts
    new_cycles = find_cycles_in_dag(updated_nodes_dict, before_field, after_field)
    
    # Verify the updated DAG has no violations with current order
    new_violations = find_constraint_violations(current_list, updated_nodes_dict, before_field, after_field)
    
    return {
        'original_violations': len(original_violations),
        'original_cycles': len(original_cycles),
        'original_cycles_detail': original_cycles,
        'cuts_needed': len(cuts),
        'cuts_list': cuts,
        'new_violations': len(new_violations),
        'new_cycles': len(new_cycles),
        'new_cycles_detail': new_cycles,
        'updated_nodes_dict': updated_nodes_dict,
        'is_dag_consistent': len(new_violations) == 0,
        'is_dag_acyclic': len(new_cycles) == 0
    }


def save_updated_constraints(
    cuts_analysis: Dict,
    output_format: str = "dict",  # "dict", "json", "summary", "cuts_only"
    before_field: str = "before",
    after_field: str = "after"
) -> str:
    """
    Format the updated constraints for saving/export.
    """
    
    if output_format == "summary":
        cuts = cuts_analysis['cuts_list']
        summary = f"Original cycles: {cuts_analysis['original_cycles']}\n"
        summary += f"Original violations: {cuts_analysis['original_violations']}\n"
        summary += f"Constraint cuts needed: {len(cuts)}\n\n"
        
        if cuts_analysis['original_cycles'] > 0:
            summary += "Original cycles found:\n"
            for i, cycle in enumerate(cuts_analysis['original_cycles_detail']):
                summary += f"  Cycle {i+1}: {' -> '.join(cycle + [cycle[0]])}\n"
            summary += "\n"
        
        if cuts:
            summary += "Edges to remove:\n"
            for from_node, to_node, constraint_ref in cuts:
                summary += f"  - Remove: {from_node} -> {to_node} (from {constraint_ref})\n"
        else:
            summary += "No cuts needed!\n"
            
        summary += f"\nResult: {cuts_analysis['new_violations']} remaining violations, "
        summary += f"{cuts_analysis['new_cycles']} remaining cycles\n"
        summary += f"DAG is {'consistent' if cuts_analysis['is_dag_consistent'] else 'inconsistent'} with ordering\n"
        summary += f"DAG is {'acyclic' if cuts_analysis['is_dag_acyclic'] else 'still has cycles'}"
        
        return summary
    
    elif output_format == "cuts_only":
        # Return a dictionary showing what was deleted from each node
        cuts = cuts_analysis['cuts_list']
        cuts_by_node = {}
        
        for from_node, to_node, constraint_ref in cuts:
            # Parse constraint_ref to get node and field (e.g., "nodeA.learn_before")
            node_name, field_name = constraint_ref.split('.', 1)
        
            if node_name not in cuts_by_node:
                cuts_by_node[node_name] = {f"{before_field}_deletes": [], f"{after_field}_deletes": []}
            
            if field_name == before_field:
                # This was a "before" constraint, so from_node was deleted from node_name's before list
                cuts_by_node[node_name][f"{before_field}_deletes"].append(from_node)
            elif field_name == after_field:
                # This was an "after" constraint, so to_node was deleted from node_name's after list
                cuts_by_node[node_name][f"{after_field}_deletes"].append(to_node)
        
        import json
        return json.dumps(cuts_by_node, indent=2)
    
    elif output_format == "json":
        import json
        return json.dumps(cuts_analysis['updated_nodes_dict'], indent=2)
    
    else:  # "dict"
        return str(cuts_analysis['updated_nodes_dict'])

if __name__ == '__main__':
    # Determine workspace root: Bazel sets BUILD_WORKSPACE_DIRECTORY, otherwise use cwd
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
    grammar_root   = os.path.join(
        workspace_root,
        'resources', 'processed', 'ai-cleaned-merge-grammars'
    )

    #Set up logging
    tlog_filename = os.path.join(grammar_root, 'summary/toposort.log')
    tlogging.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(tlog_filename)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    tlogging.addHandler(file_handler)

    # The name of the renames file
    ordered_file = os.path.join(grammar_root, 'summary/toposort-order.yaml')
    disruptions_file = os.path.join(grammar_root, 'summary/toposort-disruptions.yaml')
    suggested_cuts = os.path.join(grammar_root, 'summary/toposort-suggested-cuts.yaml')
    transitive_cuts_file = os.path.join(grammar_root, 'summary/toposort-transitive-cuts.yaml')
    changes_file = os.path.join(grammar_root, 'summary/toposort-changes.yaml')

    # Check if the disruptions file exists
    with open(ordered_file, 'r', encoding='utf-8') as f:
        existing_ordered = yaml.safe_load(f)  # Just to check if the file exists and is valid

    # Generate a grammar summary object with only learn_before and learn_after fields
    grammar_summary = generate_summary(grammar_root, ['id', 'learn_before', 'learn_after'])
    # for key in grammar_summary['all-grammar-points']:
    save_summary(grammar_summary, grammar_root, 'toposort-summary.json')

    with display.work("toposort", "updating list"):
        new_ordered, changes_made = update_priority_list_minimal(
            current_list=existing_ordered,
            nodes_dict=grammar_summary['all-grammar-points'],
            before_field='learn_before',
            after_field='learn_after',
            max_edits=10
        )

        analysis = analyze_dag_with_cuts(
            new_ordered, 
            grammar_summary['all-grammar-points'], 
            before_field='learn_before', 
            after_field='learn_after'
        )

        updated_constraints = save_updated_constraints(
            analysis, 
            output_format='cuts_only', 
            before_field='learn_before', 
            after_field='learn_after'
        )

    cuts = json.loads(updated_constraints)

    # Save the formatted cuts (not the raw cuts_list)
    with open(suggested_cuts, 'w', encoding='utf-8') as f:
        yaml.dump(cuts, f, allow_unicode=True)

    # print(updated_constraints)

    with open(ordered_file, 'w', encoding='utf-8') as f:
        yaml.dump(new_ordered, f, allow_unicode=True)

    with open(changes_file, 'w', encoding='utf-8') as f:
        yaml.dump(changes_made, f, allow_unicode=True)  

    def cut_edges(grammar_point, parsed_obj, cuts):
        # Ensure learn_before and learn_after fields always exist
        if 'learn_before' not in parsed_obj:
            parsed_obj['learn_before'] = []
        if 'learn_after' not in parsed_obj:
            parsed_obj['learn_after'] = []
            
        if grammar_point in cuts:
            edit = cuts[grammar_point]
            before = edit['learn_before_deletes'] 
            after = edit['learn_after_deletes']
            
            # Remove items to delete while preserving order
            parsed_obj['learn_before'] = [e for e in parsed_obj['learn_before'] if e not in before]
            parsed_obj['learn_after'] = [e for e in parsed_obj['learn_after'] if e not in after]
        
    def preprocess(parsed_obj, file_path):
        if parsed_obj['grammar_point'] in cuts:
            return parsed_obj
        
    def logic(parsed_obj, file_path):
        grammar_point = parsed_obj['grammar_point']
        cut_edges(grammar_point, parsed_obj, cuts)
        parsed_obj = clean_lint_memoize(parsed_obj, file_path, grammar_summary)
        return parsed_obj

    mr = MapReduce(
        input_dir            = grammar_root,
        output_dir           = grammar_root,
        preprocess_func      = preprocess,
        map_func_name        = 'cutting cycles',
        map_func             = logic,        # or a sync function
        max_threads          = 4,
    )

    asyncio.run(mr.run())

    display.stop()

    
    