import os
from grammar_summary import generate_summary, save_summary
import yaml
from collections import defaultdict, deque
import asyncio
from python.mapreduce import MapReduce
import sys
import logging

tlogging = logging.getLogger(__name__)

def find_transitive_edges(graph, ordered, edge_types):
    """
    Find edges that can be removed without changing topological order.
    Returns dict mapping source -> list of redundant edges, where each edge is:
    {'target': target_node, 'dep_type': 'learn_before'/'learn_after'}
    """
    transitive_edges = defaultdict(list)
    
    # Build position mapping for efficient ordering checks
    position = {node: i for i, node in enumerate(ordered)}
    
    for u in graph:
        direct_successors = set(graph[u])
        redundant_targets = set()  # Track which targets we've already identified as redundant
        
        # For each direct successor, find all its reachable nodes
        for v in list(direct_successors):
            if v not in graph:
                continue
                
            # DFS to find all nodes reachable from v
            reachable_from_v = set()
            stack = [v]
            visited = set()
            
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                
                for neighbor in graph.get(current, []):
                    if neighbor not in visited:
                        stack.append(neighbor)
                        reachable_from_v.add(neighbor)
            
            # Check if u has direct edges to any node reachable from v
            for w in reachable_from_v:
                if (w in direct_successors and 
                    position[v] < position[w] and 
                    w not in redundant_targets):  # Only add if not already found
                    
                    dep_type = edge_types.get((u, w), 'unknown')
                    transitive_edges[u].append({
                        'target': w,
                        'dep_type': dep_type
                    })
                    redundant_targets.add(w)  # Mark as already found
    
    return dict(transitive_edges)

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
    print(f"Toposort {tlog_filename}.")
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
        # tlogging.debug("Remaining with cycles: %s", nodes)
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
            # tlogging.debug("Appending sorted: %s", rem)
            ordered.extend(rem)
            break

        # tlogging.debug("Breaking SCC: %s", comp)
        back_count = count_back_edges(comp, graph)
        eps = 1e-6; best_edge = None; best_score = -1
        for u in comp:
            for v in graph[u]:
                if v not in comp: continue
                if (u, v) not in edge_types:
                    continue  # Skip edges that weren't in original data
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
    
    # Find transitive edges in the final DAG
    # Rebuild clean graph without the removed edges
    clean_graph = defaultdict(set)
    clean_edge_types = {}
    
    for node, deps in data.items():
        for b in deps.get('learn_before', []):
            clean_graph[b].add(node)
            clean_edge_types[(b, node)] = 'learn_before'
        for a in deps.get('learn_after', []):
            clean_graph[node].add(a)
            clean_edge_types[(node, a)] = 'learn_after'
    
    # Remove the edges we cut during cycle breaking
    for source, cuts in removed_edges.items():
        for cut in cuts:
            clean_graph[source].discard(cut['target'])
            clean_edge_types.pop((source, cut['target']), None)
    
    transitive_edges = find_transitive_edges(clean_graph, ordered, clean_edge_types)
    
    if transitive_edges:
        total_redundant = sum(len(targets) for targets in transitive_edges.values())
        tlogging.info("Found %d transitive edges that could be removed", total_redundant)
        for source, targets in transitive_edges.items():
            for target_info in targets:
                tlogging.debug("Transitive edge: %s -> %s (type=%s)", 
                             source, target_info['target'], target_info['dep_type'])

    
    return ordered, dict(removed_edges), dict(transitive_edges)


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

    # # Check if the disruptions file exists
    # with open(ordered_file, 'r', encoding='utf-8') as f:
    #     ordered = yaml.safe_load(f)  # Just to check if the file exists and is valid
        
    # forward_edges = { }
    # backward_edges = { }
    # for i, value in enumerate(ordered):
    #     if i > 0:
    #         backward_edges[value] = ordered[i-1].strip()
    #     else:
    #         backward_edges[value] = '<first>'
    #     if i < len(ordered) - 1:
    #         forward_edges[value] = ordered[i+1].strip()
    #     else:
    #         forward_edges[value] = '<last>'
            
    # def ordering_logic(parsed_obj, file_path):
    #     grammar_point = parsed_obj['grammar_point']
    #     if grammar_point not in forward_edges:
    #         raise ValueError(f"Grammar point {grammar_point} not found in forward edges")
    #     if grammar_point not in backward_edges:
    #         raise ValueError(f"Grammar point {grammar_point} not found in backward edges")
    #     parsed_obj['learn_before'] = [ backward_edges.get(grammar_point, '<first>') ]
    #     parsed_obj['learn_after'] = [ forward_edges.get(grammar_point, '<last>') ]
    #     # cut_edges(grammar_point, parsed_obj, cuts)
    #     # cut_edges(grammar_point, parsed_obj, transitive_cuts)
    #     return parsed_obj

    # mr = MapReduce(
    #     input_dir            = grammar_root,
    #     output_dir           = grammar_root,
    #     map_func_name        = 'ordering',
    #     map_func             = ordering_logic,        # or a sync function
    #     max_threads          = 4,
    # )

    # asyncio.run(mr.run())
    # sys.exit(0)



    # Generate a grammar summary object with only learn_before and learn_after fields
    grammar_summary = generate_summary(grammar_root, ['id', 'learn_before', 'learn_after'])
    for key in grammar_summary['all-grammar-points']:
        value = grammar_summary['all-grammar-points'][key]
        if value['id'] == 'gp0001':
            value['learn_before'] = []
    save_summary(grammar_summary, grammar_root, 'toposort-summary.json')

    # Perform best-effort topological sort
    print("Performing best-effort topological sort...")
    ordered,cuts,transitive_cuts = best_effort_toposort(grammar_summary['all-grammar-points'])

    # Compute forward and backward edges
    forward_edges = { }
    backward_edges = { }
    for i, value in enumerate(ordered):
        if i > 0:
            backward_edges[value] = ordered[i-1]
        if i < len(ordered) - 1:
            forward_edges[value] = ordered[i+1]


    with open(ordered_file, 'w', encoding='utf-8') as f:
        yaml.dump(ordered, f, allow_unicode=True)

    with open(suggested_cuts, 'w', encoding='utf-8') as f:
        yaml.dump(cuts, f, allow_unicode=True)

    with open(transitive_cuts_file, 'w', encoding='utf-8') as f: 
        yaml.dump(transitive_cuts, f, allow_unicode=True)

    def preprocess(parsed_obj, file_path):
        # grammar_point = parsed_obj['grammar_point']
        # if grammar_point in cuts or grammar_point in transitive_cuts:
        return parsed_obj
        
    def cut_edges(grammar_point, parsed_obj, cuts):
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
            if len(parsed_obj['learn_before']) == 0:
                if grammar_point in backward_edges:
                    parsed_obj['learn_before'] = [backward_edges[grammar_point]]
                    print(f"Added learn_before edge for {grammar_point} to {backward_edges[grammar_point]}")
            if len(parsed_obj['learn_after']) == 0:
                if grammar_point in forward_edges:
                    parsed_obj['learn_after'] = [forward_edges[grammar_point]]
        
    def logic(parsed_obj, file_path):
        grammar_point = parsed_obj['grammar_point']
        parsed_obj['learn_before'] = [ backward_edges.get(grammar_point, '<first>') ]
        parsed_obj['learn_after'] = [ forward_edges.get(grammar_point, '<last>') ]
        # cut_edges(grammar_point, parsed_obj, cuts)
        # cut_edges(grammar_point, parsed_obj, transitive_cuts)
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
    
    