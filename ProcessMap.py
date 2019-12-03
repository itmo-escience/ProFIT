import graphviz as gv
from util_pm import *

class ProcessMap(object):
    """ Perform process model from event log.
    
    Attributes
    ----------
    T: dict
        Transition matrix
    nodes: list
        Set of activities in the model
    edges: list
        Set of transitions in the model
    rates: dict
        Activity and path rates of the model
    
    See Also
    ---------
    process_map
    pm_optimized
    
    Examples
    --------
    >>> log = Log("../PATH/LOG-FILE.csv")
    >>> pm = ProcessMap(log, 100, 5)
    >>> pm_opt = ProcessMap(log, optimized=True)
    """
    def __init__(self, log, activity_rate=100, path_rate=100, optimized=False, lambd=1, step=10):
        """ Class Constructor. 
        
        Provides optimized process model if optimized=True, else
        performs model simplification based on specified rates.
        
        Parameters
        ----------
        log: Log
            Ordered records of events
        activity_rate: float
            The inverse value to node significance threshold: the
            more it is, the more activities are observed in the model
            (default 100)
        path_rate: float
            The inverse value to edge significance threshold: the
            more it is, the more transitions are observed in the model
            (default 100)
        optimized: bool
            Find optimal rates for process model (default False)
        lambd: float
            Regularization coefficient of completeness and comprehension
            of process model (default 1)
        step: int / float / list
            The step value or list of grid points for the search space
            (default 10)
        """
        if optimized:
            self.T, self.nodes, self.edges, self.rates = pm_optimized(log, lambd, step)
        else:
            self.T, self.nodes, self.edges = process_map(log, activity_rate, path_rate)
            self.rates = {'activities': activity_rate, 'paths': path_rate}

    def cycles_search(self):
        """
        Perform DFS for cycles search in graph (process model).
        
        Returns
        =======
        List: of cycles found in the graph
        """
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
        """
        Replay log and count occurrence of cycles found
        in the process model.
        
        Parameters
        ----------
        log: Log
            Ordered records of events to replay
        
        Returns
        =======
        Dict: with cycle as key and its occurrence frequency
              in the log as value
        
        See Also
        --------
        cycles_search
        """
        cycles = self.cycles_search()
        cycles_nodes = {c for cyc in cycles for c in cyc}
        cycle_count = {tuple(c) : 0 for c in cycles}
        
        cycle_event = dict()
        for v in cycles_nodes:
            tmp = [c for c in cycles if v in c]
            cycle_event[v] = tmp
        
        for case_id in log.cases:
            case_log = log.flat_log[case_id]
            i = 0
            while i < len(case_log):
                event = case_log[i]
                if event in cycle_event:
                    for c in cycle_event[event]:
                        if (len(c) >= 2):
                            j = i + 1
                            k = c.index(event)
                            k = k % (len(c) - 1) if k == len(c) - 1 else k + 1
                            for l in range(len(c)):
                                found = False
                                try: next_event = case_log[j]
                                except: break
                                if (next_event == c[k]):
                                    found = True
                                    j += 1
                                    k = k % (len(c) - 1) if k == len(c) - 1 else k + 1
                                else: break
                            if found:
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

    def render(self, save_path='', colored=True):
        """
        Visualize process model as a graph.
        
        Parameters
        ----------
        save_path: str
            Path to directory where to save result as PNG/GV file.
            If empty string (default) is passed result won't be saved
        colored: bool
            Use color map (default True) for visualization. If False
            use black and white representation
        
        Returns
        =======
        Digraph: description in the DOT language (graphviz module)
        """
        T, nodes, edges, rates = self.T, self.nodes, self.edges, self.rates
        G = gv.Digraph(strict=False, format='png')
        G.attr(rankdir='TD')
        G.attr('edge', fontname='Sans Not-Rotated 14')
        G.attr('node', shape='box', style='filled', fontname='Sans Not-Rotated 14')
        
        # 1. Node color and shape
        F = {a: sum([v[0] for v in T[a].values()]) for a in nodes} # Activities absolute frequencies
        case_cnt = sum([v[0] for v in T['start'].values()])
        x_max, x_min = max(F.values()), min(F.values())
        for a in nodes:
            node_label = a + ' (' + str(F[a]) + ')'
            color = int((x_max - F[a]) / (x_max - x_min + 1e-6) * 100.)
            fill, font = "#ffffff", 'black'
            if colored:
                for interval in color_map:
                    if color in interval:
                        fill = color_map[interval]
                        break
            else: fill = 'gray' + str(color)
            if color < 50:
                font = 'white'
            G.node(a, label=node_label, fillcolor=fill, fontcolor=font)
        G.node("start", shape="circle", label=str(case_cnt), \
                fillcolor="#95d600" if colored else "#ffffff", margin='0.05')
        G.node("end", shape="doublecircle", label='', \
                fillcolor="#ea4126" if colored else "#ffffff")
        
        # 2. Edge thickness and style
        values = [T[a_i][a_j][0] for a_i in T for a_j in T[a_i] if (a_i in nodes) & (a_j in nodes)]
        if values: t_min, t_max = min(values), max(values)
        for e in edges:
            try: edge_label = T[e[0]][e[1]][0]
            except:
                G.edge(e[0], e[1], style='dotted')
            if (e[0] == 'start') | (e[1] == 'end'):
                G.edge(e[0], e[1], label=str(edge_label), style='dashed')
            else:
                y = 1.0 + (5.0 - 1.0) * (edge_label - t_min) / (t_max - t_min + 1e-6)
                G.edge(e[0], e[1], label=str(edge_label), penwidth=str(y))
        
        if save_path:
            gv_format_save = input("Save in GV format as well as in PNG? (y/n): ").lower() == 'y'
            save_name = "process_map_activities="+str(rates['activities']) \
            			+"%_paths="+str(rates['paths'])+"%"
            G.render(save_path + save_name, view=False)
            if not gv_format_save:
                os.remove(save_path + save_name)
        
        return G
