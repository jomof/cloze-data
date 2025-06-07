import os
from grammar_summary import generate_summary, save_summary
import yaml
from collections import defaultdict, deque
import asyncio
from python.mapreduce import MapReduce

import logging

# Configure logging to file
tlog_filename = os.getenv('TOPOSORT_LOG', 'toposort.log')
tlogging = logging.getLogger(__name__)
tlogging.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(tlog_filename)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
tlogging.addHandler(file_handler)


def best_effort_toposort(data):
    """
    Perform a best-effort topological sort, breaking cycles by pruning edges
    that participate most in back-edges and originate from the lowest-priority nodes.

    :param data: dict mapping node -> { 'learn_before': [...], 'learn_after': [...], 'id': priority_str }
    :return: tuple (ordered_list, removed_edges_dict)
             where removed_edges_dict maps each 'source' node to a list of edits,
             each edit being a dict with keys:
               - 'target': the node to which the edge pointed
               - 'dep_type': either 'learn_before' or 'learn_after'
    """
    tlogging.debug("Starting best-effort topological sort on %d nodes", len(data))
    # 0) Compute priority ranking based on sorted 'id's
    all_ids = sorted({deps.get('id', '') for deps in data.values() if deps.get('id', '') is not None})
    id_to_rank = {id_str: idx for idx, id_str in enumerate(all_ids)}

    # 1) Build adjacency, indegree, and record original dependency types
    graph = defaultdict(set)
    indegree = defaultdict(int)
    priority = {}
    edge_types = {}  # (u, v) -> 'learn_before' or 'learn_after'

    for node, deps in data.items():
        priority[node] = id_to_rank.get(deps.get('id', ''), len(all_ids))
        indegree.setdefault(node, 0)
        graph.setdefault(node, set())

    for node, deps in data.items():
        for b in deps.get('learn_before', []):
            graph[b].add(node)
            indegree[node] += 1
            indegree.setdefault(b, 0)
            edge_types[(b, node)] = 'learn_before'
        for a in deps.get('learn_after', []):
            graph[node].add(a)
            indegree[a] += 1
            indegree.setdefault(a, 0)
            edge_types[(node, a)] = 'learn_after'

    # Ensure priority for all dependency-only nodes
    for n in list(graph):
        if n not in priority:
            priority[n] = len(all_ids)
            tlogging.warning("Node '%s' appeared only in dependencies; assigning default lowest priority", n)

    # 2) Standard Kahn initialization
    queue = deque(n for n, deg in indegree.items() if deg == 0)
    ordered = []
    removed_edges = defaultdict(list)

    def tarjan_scc(nodes, graph):
        """Tarjan's algorithm to find SCCs in subgraph induced by nodes"""
        index, lowlink = {}, {}
        onstack, stack, sccs = set(), [], []
        idx = 0

        def dfs(u):
            nonlocal idx
            index[u] = lowlink[u] = idx; idx += 1
            stack.append(u); onstack.add(u)
            for v in graph[u]:
                if v not in nodes: continue
                if v not in index:
                    dfs(v); lowlink[u] = min(lowlink[u], lowlink[v])
                elif v in onstack:
                    lowlink[u] = min(lowlink[u], index[v])
            if lowlink[u] == index[u]:
                comp = []
                while True:
                    w = stack.pop(); onstack.remove(w)
                    comp.append(w)
                    if w == u: break
                sccs.append(comp)

        for u in nodes:
            if u not in index: dfs(u)
        return sccs

    def count_back_edges(scc_nodes, graph):
        """Count back-edges inside the SCC via DFS"""
        color = {u: 'white' for u in scc_nodes}
        back_count = defaultdict(int)

        def dfs(u):
            color[u] = 'gray'
            for v in graph[u]:
                if v not in scc_nodes: continue
                if color[v] == 'white': dfs(v)
                elif color[v] == 'gray': back_count[(u, v)] += 1
            color[u] = 'black'

        for u in scc_nodes:
            if color[u] == 'white': dfs(u)
        return back_count

    # 3) Drain zero-indegree nodes
    while queue:
        n = queue.popleft(); ordered.append(n)
        for succ in list(graph[n]):
            graph[n].remove(succ)
            indegree[succ] -= 1
            if indegree[succ] == 0: queue.append(succ)
        graph.pop(n, None)

    # 4) Break cycles
    while graph:
        nodes = list(graph.keys())
        tlogging.debug("Remaining with cycles: %s", nodes)
        sccs = tarjan_scc(nodes, graph)
        comp = next((c for c in sccs if len(c) > 1), None)
        if not comp:
            try:
                rem = sorted(nodes, key=lambda x: (indegree[x], priority[x], x))
            except KeyError as e:
                missing = [n for n in nodes if n not in priority]
                raise KeyError(
                    f"Missing priority for {e.args[0]}. Nodes: {nodes}. Missing: {missing}"
                ) from e
            tlogging.debug("Appending sorted: %s", rem)
            ordered.extend(rem)
            break

        tlogging.debug("Breaking SCC: %s", comp)
        back_count = count_back_edges(comp, graph)
        eps = 1e-6; best_edge = None; best_score = -1
        for u in comp:
            for v in graph[u]:
                if v not in comp: continue
                bc = back_count.get((u, v), 0)
                score = (bc + 1) / (priority[u] + eps)
                if score > best_score:
                    best_score, best_edge = score, (u, v)
        u, v = best_edge if best_edge else (comp[0], next(iter(graph[comp[0]])))
        graph[u].remove(v); indegree[v] -= 1
        dep_type = edge_types.get((u, v), 'unknown')
        removed_edges[u].append({'target': v, 'dep_type': dep_type})
        tlogging.info("Pruned edge %s -> %s (type=%s)", u, v, dep_type)

        queue = deque(n for n, deg in indegree.items() if deg == 0 and n in graph)
        while queue:
            n2 = queue.popleft(); ordered.append(n2)
            for succ in list(graph[n2]):
                graph[n2].remove(succ)
                indegree[succ] -= 1
                if indegree[succ] == 0: queue.append(succ)
            graph.pop(n2, None)

    tlogging.debug("Complete. Ordered %d, cut %d.", len(ordered), sum(len(v) for v in removed_edges.values()))
    return ordered, dict(removed_edges)


if __name__ == '__main__':
    # Determine workspace root: Bazel sets BUILD_WORKSPACE_DIRECTORY, otherwise use cwd
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
    grammar_root   = os.path.join(
        workspace_root,
        'resources', 'processed', 'ai-cleaned-merge-grammars'
    )

    # The name of the renames file
    ordered_file = os.path.join(grammar_root, 'summary/toposort-order.yaml')
    disruptions_file = os.path.join(grammar_root, 'summary/toposort-disruptions.yaml')
    suggested_cuts = os.path.join(grammar_root, 'summary/toposort-suggested-cuts.yaml')
    tlog_filename = os.path.join(grammar_root, 'summary/toposort.log')

    # Generate a grammar summary object with only learn_before and learn_after fields
    grammar_summary = generate_summary(grammar_root, ['id', 'learn_before', 'learn_after'])
    for key in grammar_summary['all-grammar-points']:
        value = grammar_summary['all-grammar-points'][key]
        if value['id'] == 'gp0001':
            value['learn_before'] = []
    save_summary(grammar_summary, grammar_root, 'toposort-summary.json')

    # Perform best-effort topological sort
    print("Performing best-effort topological sort...")
    ordered,cuts = best_effort_toposort(grammar_summary['all-grammar-points'])
    with open(ordered_file, 'w', encoding='utf-8') as f:
        yaml.dump(ordered, f, allow_unicode=True)

    with open(suggested_cuts, 'w', encoding='utf-8') as f:
        yaml.dump(cuts, f, allow_unicode=True)

    def preprocess(parsed_obj, file_path):
        grammar_point = parsed_obj['grammar_point']
        if grammar_point in cuts:
            return parsed_obj
        
    def logic(parsed_obj, file_path):
        grammar_point = parsed_obj['grammar_point']
        if grammar_point in cuts:
            for edit in cuts[grammar_point]:
                dep_type = edit['dep_type']
                target = edit['target']
                if dep_type not in parsed_obj:
                    raise ValueError(f"Unexpected dependency type: {dep_type}")
                # if target not in parsed_obj[dep_type]:
                #     raise ValueError(f"Target {target} not found in {dep_type} of {grammar_point}")
                if target in parsed_obj[dep_type]:
                    parsed_obj[dep_type].remove(target)
        return parsed_obj

    mr = MapReduce(
        input_dir            = grammar_root,
        output_dir           = grammar_root,
        preprocess_func      = preprocess,
        map_func_name        = 'cutting cycles',
        map_func             = logic,        # or a sync function
        max_threads          = 4,
    )

    # asyncio.run(mr.run())
    
    