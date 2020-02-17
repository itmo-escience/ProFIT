color_map = {range(0,10) : "#1d2559", range(10,20) : "#203078",
             range(20,30) : "#1f3b98", range(30,40) : "#1946ba",
             range(40,50) : "#5661c6", range(50,60) : "#7d7fd2",
             range(60,70) : "#a09dde", range(70,80) : "#c0bde9",
             range(80,90) : "#e0ddf4", range(90,101) : "#ffffff"}

def incidence_matrix(edges, excpt=[]):
    """ Perform an incidence matrix

    Returns the matrix as dict where 1 indicates a
    relationship between two nodes in a directed graph.
    
    Parameters
    ----------
    edges: list
        Set of graph's edges
    excpt: list
        Set of nodes to exclude from matrix construction
        (default [])
    """
    I = dict()
    for e in edges:
        a_i = e[0]
        a_j = e[1]
        if (a_i in excpt) | (a_j in excpt):
            continue
        if (a_i not in I):
            I[a_i] = dict()
        if (a_j not in I[a_i]):
            I[a_i][a_j] = 1
    return I

def dict_normalization(dict_, nested=False):
    """ Perform dictionary normalization as matrix's
    rows normalization
    
    Returns normalized along rows matrix as a dictionary.
    
    Parameters
    ----------
    dict_: dict
        Dictionary (array or matrix) to normalize
    nested: bool
        Indicate object dimension: if True the 2-dimensional
        object is passed, else 1-dimensional (default False)
    """
    dict_norm = dict()
    if not nested:
        d_max = max(dict_.values())
        d_min = min(dict_.values())
        if d_max - d_min == 0: 
            dict_norm = {key: 1 for key in dict_}
        else: 
            dict_norm = {key: (dict_[key] - d_min) / (d_max - d_min) for key in dict_}
    else:
        for key_1 in dict_:
            if dict_[key_1]:
                dict_norm[key_1] = dict()
            else: continue
            d_max = max(dict_[key_1].values())
            d_min = min(dict_[key_1].values())
            for key_2 in dict_[key_1]:
                if d_max - d_min == 0:
                    dict_norm[key_1][key_2] = 1 / len(dict_[key_1])
                else:
                    dict_norm[key_1][key_2] = (dict_[key_1][key_2] - d_min) / (d_max - d_min)
    return dict_norm

def node_significance(log):
    # Node case significance
    # Activities case frequencies
    caseF = dict()
    for a in log.activities:
        caseF[a] = 0
        for case_id in log.flat_log:
            if a in log.flat_log[case_id]: caseF[a] += 1
    # Activities significance
    S = {a: caseF[a] / len(log.cases) for a in caseF}
    return S

def transit_matrix(log, T):
    # Transition matrix with 'start' and 'end' nodes 
    process_start, process_end = dict(), dict()
    for case_id in log.flat_log:
        s = log.flat_log[case_id][0]
        e = log.flat_log[case_id][-1]
        if s not in process_start: process_start[s] = 0
        process_start[s] += 1
        if e not in process_end: process_end[e] = 0
        process_end[e] += 1
    T['start'] = {s: (process_start[s],process_start[s]) for s in process_start}
    for e in process_end:
        if e not in T: T[e] = dict()
        T[e]['end'] = (process_end[e],process_end[e])
    return T

def ADS_matrix(log, T):
    case_cnt = len(log.cases)
    T = transit_matrix(log, T)
    activities = log.activities
    ADS = dict()
    for v1 in list(activities)+['start']:
        ADS[v1] = dict()
        for v2 in list(activities)+['end']:
            try: f_rel = T[v1][v2][1]
            except: f_rel = -1
            if f_rel == case_cnt:
                ADS[v1][v2] = 'A' # always
            elif f_rel > 0:
                ADS[v1][v2] = 'S' # sometimes
            elif f_rel == -1:
                ADS[v1][v2] = 'N' # never
    return ADS

def edge_sig(T, source=[], target=[], type_='out'):
    # Edge case significance
    case_cnt = sum([v[0] for v in T['start'].values()])
    S = dict()
    for a_i in source:
        S[a_i] = dict()
        target_ = T if type_ != 'out' else T[a_i]
        for a_j in target_:
            if (a_i == a_j) | (a_j not in target): continue
            if type_ != 'out':
                if a_i in T[a_j]: S[a_i][a_j] = T[a_j][a_i][1] / case_cnt
            else: S[a_i][a_j] = T[a_i][a_j][1] / case_cnt
    return S

def rel_sig(S_out, S_in):
    # Relative significance of conflicting relations
    rS = dict()
    for A in S_out:
        rS[A] = dict()
        for B in S_out[A]:
            if A in S_in:
                if B in S_in[A]:
                    sigAX = sum(S_out[A].values())
                    sigXB = sum(S_in[B].values())
                    rS[A][B] = .5 * S_out[A][B] / sigAX + .5 * S_out[A][B] / sigXB
    return rS

def conflict_resolution(rS, pth=0.3, rth=2*0.3/3):
    # Determine the most significant behavior in the process
    ttp = [] # transitions in conflict to preserve
    for A in rS:
        for B in rS[A]:
            if (rS[A][B] >= pth) & (rS[B][A] >= pth): # preserve threshold
                ttp.append(tuple([A,B]))
                ttp.append(tuple([B,A]))
            elif (abs(rS[A][B] - rS[B][A]) >= rth): # ratio threshold
                if (rS[A][B] - rS[B][A] >= 0):
                    ttp.append(tuple([A,B]))
                else:
                    ttp.append(tuple([B,A]))
    return set(ttp)

def edge_filtering(S, edge_list, co=0, type_='out'):
    """ Process model simplification

    Returns filtrated set of edges.

    Parameters
    ----------
    S: dict
        Edge significance matrix
    edge_list: list
        Set of edges to filtrate
    co: float
        Cut-off threshold for edge filtration
        (default 0)
    type_: str
        Determine type of edges (in- or outcoming)
        to filtrate (default 'out')
    """
    edges = edge_list[:]
    for a in S:
        S_sort = sorted(S[a], key=S[a].get, reverse=True)
        for i in range(len(S[a])):
            b = S_sort[i]
            if (S[a][b] >= co) | (i == 0):
                if type_ != 'out':
                    if ((b,a) not in edges): edges.append((b,a))
                else:
                    if ((a,b) not in edges): edges.append((a,b))
            else: break
    return edges

def make_connected(edges, T, I, S, S_out, state, check_cond='desc'):
    # Find extra edges if condition fails. See also: check_feasibility
    component_nodes = [k for k,v in state.items() if v == False]
    directed_nodes = [k for k,v in state.items() if v == True]
    source = directed_nodes if check_cond == 'desc' else component_nodes
    target = component_nodes if check_cond == 'desc' else directed_nodes
    extra_edges = dict()
    for node in source:
        for a in T[node]:
            if a in target:
                extra_edges[(node,a)] = S_out[node][a]
    if len(extra_edges) == 0:
        S_comp = {k:v for k,v in S.items() if k in component_nodes}
        if check_cond == 'desc':
            edges.append(('start', max(S_comp, key=S_comp.get)))
            if 'start' not in I:
                I['start'] = dict()
            I['start'][max(S_comp, key=S_comp.get)] = 1
        else:
            edges.append((max(S_comp, key=S_comp.get), 'end'))
            if max(S_comp, key=S_comp.get) not in I:
                I[max(S_comp, key=S_comp.get)] = dict()
            I[max(S_comp, key=S_comp.get)]['end'] = 1
    else:
        extra_edge = max(extra_edges, key=extra_edges.get)
        edges.append((extra_edge[0], extra_edge[1]))
        if extra_edge[0] not in I:
            I[extra_edge[0]] = dict()
        I[extra_edge[0]][extra_edge[1]] = 1

def check_feasibility(nodes, edges, T, I, S, S_out):
    # Perform two DFS types to check conditions:
    # 1. All nodes are end ancestors
    def isAncestor(start, node):
        marked[node] = True
        try: successors = I[node]
        except: successors = []
        if 'end' in successors:
            end_ancestor[start] = True
        if end_ancestor[start] == False:
            for successor in successors:
                if marked[successor] == False:
                    isAncestor(start, successor)
    while True:
        end_ancestor = dict.fromkeys(nodes, False)
        for v in nodes:
            marked = dict.fromkeys(nodes, False)
            isAncestor(v, v)
        if all(end_ancestor.values()): break
        else: make_connected(edges, T, I, S, S_out, end_ancestor, 'anc')
    # 2. All nodes are start descendants
    def isDescendant(node):
        start_descendant[node] = True
        try: successors = I[node]
        except: successors = []
        for successor in successors:
            if successor != 'end':
                if start_descendant[successor] == False:
                    isDescendant(successor)
    while True:
        start_descendant = dict.fromkeys(nodes, False)
        isDescendant('start')
        if all(start_descendant.values()): break
        else: make_connected(edges, T, I, S, S_out, start_descendant, 'desc')

def reconstruct_log(log, meta_states):
    meta_states.sort(key=len, reverse=True)
    states_seq = {s: [s[i:len(s)]+s[0:i] for i in range(len(s))] \
                                         for s in meta_states}
    log1 = dict()
    for case in log.flat_log:
        case_log = log.flat_log[case]
        case_log1 = []
        aggregated = False
        i = 0
        while i < len(case_log):
            for s in meta_states:
                try: tmp = case_log[i:i+len(s)]
                except: continue
                if tmp == s:
                    case_log1.append(s)
                    i += len(s) - 1
                    aggregated = True
                    break
            if not aggregated:
                case_log1.append(case_log[i])
            i += 1
            aggregated = False
        log1[case] = tuple(case_log1)
    
    return log1