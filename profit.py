import os, sys
import pandas as pd
import graphviz as gv

class Log(object):
    
    def __init__(self, data_path, cols=(0,1), *args, **kwargs):
        log = pd.read_csv(data_path, usecols=cols, *args, **kwargs)
        log.columns = ['case_id', 'activity']
        log.set_index('case_id', drop=True, inplace=True)
        self.flat_log = dict(log.activity.groupby(level=0).agg(tuple))
        self.cases = set(log.index)
        self.activities = set(log.activity)
    
    def transit_matrix(self):
        T = dict()
        to_add = dict()
        for case_id in self.flat_log:
            for i in range(len(self.flat_log[case_id]) - 1):
                a_i = self.flat_log[case_id][i]
                a_j = self.flat_log[case_id][i+1]
                if a_i not in T:
                    T[a_i] = dict()
                    to_add[a_i] = dict()
                if a_j not in T[a_i]:
                    T[a_i][a_j] = [0, 0]
                    to_add[a_i][a_j] = True
                T[a_i][a_j][0] += 1
                if to_add[a_i][a_j]:
                    T[a_i][a_j][1] += 1
                    to_add[a_i][a_j] = False
            for a_i in to_add:
                for a_j in to_add[a_i]:
                    to_add[a_i][a_j] = True
        for a_i in T:
            for a_j in T[a_i]:
                T[a_i][a_j] = tuple(T[a_i][a_j])
        return T
    
    def incidence_matrix(self):
        T = self.transit_matrix()
        I = dict()
        for activity in self.activities:
            I[activity] = dict.fromkeys(self.activities, False)
            if activity in T:
                for a in self.activities:
                    if a in T[activity]: I[activity][a] = True
        return I
    
    def process_map(self, activity_rate, path_rate):
        
        assert 0 <= activity_rate <= 100, "Activity rate is out of range (it should be from 0 to 100)"
        assert 0 <= path_rate <= 100, "Path rate is out of range (it should be from 0 to 100)"
        
        # Util for data normalization
        def dict_normalization(dict_, nested=False):
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
                    dict_norm[key_1] = dict()
                    d_max = max(dict_[key_1].values())
                    d_min = min(dict_[key_1].values())
                    for key_2 in dict_[key_1]:
                        if d_max - d_min == 0:
                            dict_norm[key_1][key_2] = 1 / len(dict_[key_1])
                        else:
                            dict_norm[key_1][key_2] = (dict_[key_1][key_2] - d_min) / (d_max - d_min)
            return dict_norm
        
        # 1. Node filtering
        
        def node_significance():        
            # Activities case frequencies
            caseF = dict()
            for a in self.activities:
                caseF[a] = 0
                for case_id in self.flat_log:
                    if a in self.flat_log[case_id]: caseF[a] += 1
            # Activities significance
            S = {a: caseF[a] / len(self.cases) for a in caseF}
            return S
        
        S = dict_normalization(node_significance(), nested=False)
        activities = [a for a in S if (S[a] >= (100 - activity_rate) / 100)]
        
        # 2. Edge filtering
        
        # Transition matrix with 'start' and 'end' nodes
        def transit_matrix_(T):
            process_start, process_end = dict(), dict()
            for case_id in self.flat_log:
                s = self.flat_log[case_id][0]
                e = self.flat_log[case_id][-1]
                if s not in process_start: process_start[s] = 0
                process_start[s] += 1
                if e not in process_end: process_end[e] = 0
                process_end[e] += 1
            T['start'] = {s: (process_start[s],process_start[s]) for s in process_start}
            for e in process_end:
                if e not in T: T[e] = dict()
                T[e]['end'] = (process_end[e],process_end[e])  
            return T
        
        T = transit_matrix_(self.transit_matrix())
        
        # Early algorithm stop
        if (path_rate == 100):
            transitions = [(a_i, a_j) for a_i in T for a_j in T[a_i] \
                           if (a_i in activities + ['start', 'end']) & (a_j in activities + ['start', 'end'])]
            if sys._getframe(1).f_code.co_name == '__init__':
                return T, activities, transitions
            return activities, transitions
        
        def edge_sig(T, source=[], target=[], type_='out'):
            S = dict()
            for a_i in source:
                S[a_i] = dict()
                target_ = T if type_ != 'out' else T[a_i]
                for a_j in target_:
                    if (a_i == a_j) | (a_j not in target): continue
                    if type_ != 'out':
                        if a_i in T[a_j]: S[a_i][a_j] = T[a_j][a_i][1] / len(self.cases)
                    else: S[a_i][a_j] = T[a_i][a_j][1] / len(self.cases)
            return S
        
        # Significance matrix of outcoming edges
        S_out = edge_sig(T, source=activities + ['start'], target=activities + ['end'], type_='out')
        # Significance matrix of incoming edges (inverse outcoming)
        S_in = edge_sig(T, source=activities + ['end'], target=activities + ['start'], type_='in')      
        # Self-loops case significance
        S_loop = {a_i: T[a_i][a_j][1] / len(self.cases) for a_i in T for a_j in T[a_i] \
                  if (a_i == a_j) & (a_i in activities)}
        # Evaluate the relative significance of conflicting relations
        rS = dict()
        for A in S_out:
            rS[A] = dict()
            for B in S_out[A]:
                if A in S_in:
                    if B in S_in[A]:
                        sigAX = sum(S_out[A].values())
                        sigXB = sum(S_in[B].values())
                        rS[A][B] = .5 * S_out[A][B] / sigAX + .5 * S_out[A][B] / sigXB
        
        # Normalization
        S_out = dict_normalization(S_out, nested=True)
        S_in = dict_normalization(S_in, nested=True)
        S_loop = dict_normalization(S_loop)
        
        co = (100 - path_rate) / 100 # cut-off threshold
        
        def conflict_resolution(rS, pth=0.3, rth=2*0.3/3):
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
        
        transitions = list(conflict_resolution(rS))
        
        def edge_filtering(S, edge_list, type_='out'):
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
        
        transitions = edge_filtering(S_in, transitions, type_='in')
        transitions = edge_filtering(S_out, transitions, type_='out')
        
        for a_i in S_loop:
            if (S_loop[a_i] - 0.01 >= co) | (co == 0):
                transitions.append((a_i,a_i))
                
        # 3. Check graph connectivity
        
        I = dict() # Filtered incidence matrix
        for t in transitions:
            a_i = t[0]
            a_j = t[1]
            if (a_i not in I):
                I[a_i] = dict()
            if (a_j not in I[a_i]):
                I[a_i][a_j] = 1
        
        def check_connectivity(I, state, check_func):
            while not all(state):
                component_nodes = [k for k,v in state.items() if v == False]
                directed_nodes = [k for k,v in state.items() if v == True]
                source = directed_nodes if check_func == DFS else component_nodes
                target = component_nodes if check_func == DFS else directed_nodes
                extra_edges = dict()
                for node in source:
                    for a in I[node]:
                        if a in target:
                            extra_edges[(node,a)] = S_out[node][a]
                if len(extra_edges) == 0:
                    S_comp = {k:v for k,v in S.items() if k in component_nodes}
                    if check_func == DFS:
                        transitions.append(('start', max(S_comp, key=S_comp.get)))
                        if 'start' not in I:
                            I['start'] = dict()
                        I['start'][max(S_comp, key=S_comp.get)] = 1
                    else:
                        transitions.append((max(S_comp, key=S_comp.get), 'end'))
                        if max(S_comp, key=S_comp.get) not in I:
                            I[max(S_comp, key=S_comp.get)] = dict()
                        I[max(S_comp, key=S_comp.get)]['end'] = 1
                else:
                    extra_edge = max(extra_edges, key=extra_edges.get)
                    transitions.append((extra_edge[0], extra_edge[1]))
                    if extra_edge[0] not in I:
                        I[extra_edge[0]] = dict()
                    I[extra_edge[0]][extra_edge[1]] = 1
                
                if check_func == DFS:
                    state = dict.fromkeys(activities, False)
                    DFS('start')
                else: state = check_completion()
        
        # 3.1 Check all nodes are end ancestors
        def check_completion():
            
            def DFS(start, node):
                marked[node] = True
                try: successors = I[node]
                except: successors = []
                if 'end' in successors:
                    end_ancestor[start] = True
                if end_ancestor[start] == False:
                    for successor in successors:
                        if marked[successor] == False:
                            DFS(start, successor)
            
            end_ancestor = dict.fromkeys(activities, False)
            for a in activities:
                marked = dict.fromkeys(activities, False)
                DFS(a, a)
            return end_ancestor
        
        check_connectivity = (I, check_completion(), check_completion)
        
        # 3.2 Check all nodes are start descendants
        def DFS(node):
            start_descendant[node] = True
            try: successors = I[node]
            except: successors = []
            for successor in successors:
                if successor != 'end':
                    if start_descendant[successor] == False:
                        DFS(successor)
        
        start_descendant = dict.fromkeys(activities, False)
        DFS('start')
        check_connectivity = (I, start_descendant, DFS)
        
        if sys._getframe(1).f_code.co_name == '__init__':
            return T, activities, transitions
        
        return activities, transitions

class ProcessMap(object):
    
    def __init__(self, log, activity_rate, path_rate):
        self.T, self.nodes, self.edges = log.process_map(activity_rate, path_rate)
    
    def render(self, save='', colored=True):
        T, nodes, edges = self.T, self.nodes, self.edges
        G = gv.Digraph(strict=False, format='png')
        G.graph_attr['rankdir'] = 'TD'
        G.node_attr['shape'] = 'box'
        G.node_attr['fontname'] = "Sans Not-Rotated 14"
        G.edge_attr['fontname'] = "Sans Not-Rotated 14"
        
        # Node color and shape
        F = dict() # Activities absolute frequencies
        for a in nodes:
            F[a] = sum([v[0] for v in T[a].values()])
        x_max = max(F.values())
        x_min = min(F.values())
        
        if colored: color_map = {range(0,10) : "#ffffff", range(10,20) : "#e0ddf4",
                                 range(20,30) : "#c0bde9", range(30,40) : "#a09dde",
                                 range(40,50) : "#7d7fd2", range(50,60) : "#5661c6",
                                 range(60,70) : "#1946ba", range(70,80) : "#1f3b98",
                                 range(80,90) : "#203078", range(90,101) : "#1d2559"}
        for a in nodes:
            node_label = a + ' (' + str(F[a]) + ')'
            color = int((F[a] - x_min) / (x_max - x_min + 1e-6) * 100.)
            fill = "#ffffff"
            if colored:
                for interval in color_map:
                    if color in interval:
                        fill = color_map[interval]
                        break
            else: fill = 'gray' + str(color)
            font = 'black'
            if (color >= 50):
                font = 'white'
            G.node(a, label=node_label, style='filled', fillcolor=fill, fontcolor=font)
        
        num_cases = sum([v[0] for v in T['start'].values()])
        fill_start = "#95d600" if colored else "#ffffff"
        fill_end = "#ea4126" if colored else "#ffffff"
        
        G.node("start", shape="circle", label=str(num_cases), style='filled', fillcolor=fill_start, margin='0.05')
        G.node("end", shape="doublecircle", label='', style='filled', fillcolor=fill_end)
        
        # Edge thickness and style
        values = [T[a_i][a_j][0] for a_i in T for a_j in T[a_i] if (a_i in nodes) & (a_j in nodes)]
        if values: t_min, t_max = min(values), max(values)
        
        for e in edges:
            if (e[0] == 'start'):
                if e[1] not in T[e[0]]:
                    G.edge(e[0], e[1], style='dotted')
                else:
                    G.edge(e[0], e[1], label=str(T[e[0]][e[1]][0]), style='dashed')
            elif (e[1] == 'end'):
                if e[1] not in T[e[0]]: 
                    G.edge(e[0], e[1], style='dotted')
                else: 
                    G.edge(e[0], e[1], label=str(T[e[0]][e[1]][0]), style='dashed')
            else:
                y = 1.0 + (5.0 - 1.0) * (T[e[0]][e[1]][0] - t_min) / (t_max - t_min + 1e-6)
                G.edge(e[0], e[1], label=str(T[e[0]][e[1]][0]), penwidth=str(y))
        
        if save:
            gv_format_save = input("Save in GV format as well as in PNG? (y/n): ").lower() == 'y'
            G.render(save + "process_map_activities="+str(activity_rate)+"%_paths="+str(path_rate)+"%")
            if not gv_format_save:
                os.remove(save + "process_map_activities="+str(activity_rate)+"%_paths="+str(path_rate)+"%")
        
        return G
    
    def cycles_search(self):
        
        def incidence_matrix(edges):
            I = dict()
            for e in edges:
                a_i = e[0]
                a_j = e[1]
                if (a_i == 'start') | (a_j == 'end'):
                    continue
                if (a_i not in I):
                    I[a_i] = dict()
                if (a_j not in I[a_i]):
                    I[a_i][a_j] = 1
            return I
        
        G = incidence_matrix(self.edges)
        cycles = []
        stack = []
        
        def DFS(start, node):
            visited[node] = True
            stack.append(node)
            
            try: successors = G[node]
            except: successors = []
            
            for successor in successors:
                if marked[successor] == True:
                    G[successor] = dict()
                elif visited[successor] == False:
                    DFS(start, successor)
                elif successor == start:
                    cycles.append(list(stack))
            
            stack.pop()
            visited[node] = False
        
        marked = dict.fromkeys(self.nodes, False)
        for v in self.nodes:
            visited = dict.fromkeys(self.nodes, False)
            DFS(v, v)
            marked[v] = True
        
        return cycles
    
    def cycles_replay(self, log):
        cycles = self.cycles_search()
        cycles_nodes = set([c[i] for c in cycles for i in range(len(c))])
        
        cycle_count = dict()
        for c in cycles:
            cycle_count[tuple(c)] = 0
        
        cycle_event = dict()
        for v in cycles_nodes:
            tmp = []
            for c in cycles:
                if (v in c):
                    tmp.append(c)
            cycle_event[v] = tmp
        
        for case_id in log.cases:
            case_log = log.flat_log[case_id]
            i = 0
            while i < len(case_log):
                event = case_log[i]
                if event in cycle_event:
                    for c in cycle_event[event]:
                        if (len(c) >= 2):
                            f = False
                            j = i + 1
                            k = (c.index(event)) % (len(c) - 1) if (c.index(event) == len(c) - 1) else c.index(event) + 1
                            for l in range(len(c)):
                                try: next_event = case_log[j]
                                except:
                                    f = False
                                    break
                                if (next_event == c[k]):
                                    f = True
                                    j += 1
                                    k = (k % (len(c) - 1)) if (k == len(c) - 1) else k + 1
                                else:
                                    f = False
                                    break
                            if f:
                                cycle_count[tuple(c)] += 1
                                i += len(c) - 1
                                break
                        else:
                            try: next_event = case_log[i + 1]
                            except: continue
                            if (event == next_event):
                                cycle_count[tuple(c)] += 1
                                break
                i += 1
        
        return cycle_count
