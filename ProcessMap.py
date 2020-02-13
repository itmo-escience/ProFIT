import graphviz as gv
from util_pm import *

class ProcessMap(object):
    """ Discover process model from event log.
    
    Attributes
    ----------
    T: dict
        Transition matrix
    nodes: dict
        Activities in the model and their frequencies
        (absolute and case)
    edges: dict
        Transitions in the model and their frequencies
        (absolute and case)
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
    def __init__(self, log, activity_rate=100, path_rate=100, aggregate=False, optimized=False, lambd=1, step=10):
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
        aggregate: bool
            Aggregate activities into meta-states (default False)
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
        if aggregate:
            SC = find_states(log, self)
            fl, log.flat_log = log.flat_log, reconstruct_log(log, SC)
            av, log.activities = log.activities, log.activities.union(set(SC))
            _, self.nodes, self.edges = process_map(log, activity_rate, path_rate)
            log.flat_log = fl
    
    def paths_search(self, source, target):
        G = incidence_matrix(self.edges, ['start', 'end'])
        paths = []
        stack = [source]
        
        def DFS(node, end):
            visited[node] = True
            stack.append(node)
            
            try: successors = G[node]
            except: successors = []
            
            for successor in successors:
                if successor == end:
                    paths.append(list(stack)+[end])
                elif marked[successor] == True:
                    G[successor] = dict()
                elif visited[successor] == False:
                    DFS(successor, end)
            
            stack.pop()
            visited[node] = False
        
        marked = dict.fromkeys(self.nodes, False)
        for v in G[source]:
            if v == source: continue
            if v == target:
                paths.append([source, target])
                continue
            visited = dict.fromkeys(self.nodes, False)
            visited[source] = True
            DFS(v, target)
            marked[v] = True
        
        return paths

    def cycles_search(self):
        """
        Perform DFS for cycles search in graph (process model).
        
        Returns
        =======
        List: of cycles found in the graph
        """
        G = incidence_matrix(self.edges)
        nodes =  ['start', 'end'] + list(self.nodes)
        cycles = []
        stack = []
        res = []
        
        visited = dict.fromkeys(nodes, False)
        def preorder_traversal(start_node):
            visited[start_node] = True
            res.append(start_node)
            try: successors = G[start_node]
            except: successors = []
            for successor in successors:
                if not visited[successor]:
                    preorder_traversal(successor)
        
        preorder_traversal('start')
        nodes = res
        
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
                    cycles.append(tuple(stack))
            
            stack.pop()
            visited[node] = False
        
        marked = dict.fromkeys(nodes, False)
        for v in nodes:
            visited = dict.fromkeys(nodes, False)
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
        cycles.sort(key=len, reverse=True)
        cycle_count = {c : [0,0] for c in cycles}
        cycles_seq = {c: [c[i:len(c)]+c[0:i] for i in range(len(c))] \
                                             for c in cycles}
        to_add = {c: False for c in cycles}
        
        for case in log.flat_log:
            case_log = log.flat_log[case]
            i = 0
            while i < len(case_log):
                for c in cycles:
                    try: tmp = case_log[i:i+len(c)]
                    except: continue
                    if tmp == c:
                        cycle_count[c][0] += 1
                        i += len(c) - 1
                        to_add[c] = True
                        break
                i += 1
            for c in cycles:
                if to_add[c]:
                    cycle_count[c][1] += 1
                    to_add[c] = False
        
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
        G.attr(rankdir='TB')
        G.attr('edge', fontname='Sans Not-Rotated 14')
        G.attr('node', shape='box', style='filled', fontname='Sans Not-Rotated 14')
        
        # 1. Node color and shape
        F = {a: nodes[a][0] for a in nodes} # Activities absolute frequencies
        case_cnt = sum([v[0] for v in T['start'].values()])
        x_max, x_min = max(F.values()), min(F.values())
        for a in nodes:
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
            if type(a) == tuple:
                node_label = a[0]
                for i in range(1,len(a)):
                    node_label += '\n' + a[i]
                node_label += '\n(' + str(nodes[a][0]) + ')'
                G.node(str(a), label=node_label, fillcolor=fill, fontcolor=font, shape='octagon')
            else:
                node_label = a + ' (' + str(F[a]) + ')'
                G.node(a, label=node_label, fillcolor=fill, fontcolor=font)
        G.node("start", shape="circle", label=str(case_cnt), \
                fillcolor="#95d600" if colored else "#ffffff", margin='0.05')
        G.node("end", shape="doublecircle", label='', \
                fillcolor="#ea4126" if colored else "#ffffff")
        
        # 2. Edge thickness and style
        values = [edges[e][0] for e in edges]
        if values: t_min, t_max = min(values), max(values)
        for e in edges:
            if edges[e] == (0,0):
                G.edge(str(e[0]), str(e[1]), style='dotted')
                continue
            if (e[0] == 'start') | (e[1] == 'end'):
                G.edge(str(e[0]), str(e[1]), label=str(edges[e][0]), style='dashed')
            else:
                y = 1.0 + (5.0 - 1.0) * (edges[e][0] - t_min) / (t_max - t_min + 1e-6)
                G.edge(str(e[0]), str(e[1]), label=str(edges[e][0]), penwidth=str(y))
        
        if save_path:
            gv_format_save = input("Save in GV format as well as in PNG? (y/n): ").lower() == 'y'
            save_name = "process_map_activities="+str(rates['activities']) \
            			+"%_paths="+str(rates['paths'])+"%"
            G.render(save_path + save_name, view=False)
            if not gv_format_save:
                os.remove(save_path + save_name)
        
        return G
