from log import Log
from transition_matrix import TransitionMatrix
from util_func import *
import sys

class Graph():
    """Class to represent process model as a graph structure."""

    def __init__(self):
        """Graph object as a set of nodes (default None) and 
        a set of edges (default None).
        """
        self.nodes = None
        self.edges = None

    def update(self, log, activity_rate, path_rate, T):
        """Update nodes and edges attributes performing node
        and edge filtering according to activity and path rates,
        respectively.

        Parameters
        ----------
        log: Log
            Ordered records of events
        activity_rate: float
            The inverse value to node significance threshold: the
            more it is, the more activities are observed in the model
        path_rate: float
            The inverse value to edge significance threshold: the
            more it is, the more transitions are observed in the model
        T: TransitionMatrix
            A matrix describing the transitions of a Markov chain

        See Also
        ---------
        Log
        TransitionMatrix

        References
        ----------
        .. [1] Ferreira, D. R. (2017). A primer on process mining. Springer, Cham.
        .. [2] Günther, C. W., & Van Der Aalst, W. M. (2007, September). Fuzzy 
               mining–adaptive process simplification based on multi-perspective 
               metrics. In International conference on business process management 
               (pp. 328-343). Springer, Berlin, Heidelberg.
        """
        # 1. Node filtering
        S = node_significance(log)
        S_norm = dict_normalization(S, nested=False)
        activities = [a for a in S_norm if S_norm[a] >= (1-activity_rate/100)]
        
        # 2. Edge filtering
        T = transit_matrix(log, T.T)
        
        # Early algorithm stop
        if (path_rate == 100):
            transitions = [(a_i, a_j) for a_i in T for a_j in T[a_i] \
                           if (a_i in activities + ['start', 'end']) \
                           & (a_j in activities + ['start', 'end'])]
        else:
            # Significance matrix of outcoming edges
            S_out = edge_sig(T, source=activities+['start'], \
                                target=activities+['end'], type_='out')
            # Significance matrix of incoming edges (inverse outcoming)
            S_in = edge_sig(T, source=activities+['end'], \
                               target=activities+['start'], type_='in')
            # Self-loops case significance
            S_loop = {a_i: T[a_i][a_j][1] / len(log.cases) for a_i in T \
                      for a_j in T[a_i] if (a_i == a_j) & (a_i in activities)}
            # Evaluate the relative significance of conflicting relations
            rS = rel_sig(S_out, S_in)
            
            # Normalization
            S_out_norm = dict_normalization(S_out, nested=True)
            S_in_norm = dict_normalization(S_in, nested=True)
            S_loop_norm = dict_normalization(S_loop)
            
            co = 1 - path_rate / 100 # cut-off threshold
            transitions = list(conflict_resolution(rS)) # initial set of transitions to preserve    
            transitions = edge_filtering(S_in_norm, transitions, co=co, type_='in')
            transitions = edge_filtering(S_out_norm, transitions, co=co, type_='out')
            for a_i in S_loop_norm:
                if (S_loop_norm[a_i] - 0.01 >= co) | (co == 0):
                    transitions.append((a_i,a_i))
            
            # 3. Check graph connectivity
            I = incidence_matrix(transitions) # Filtered incidence matrix
            check_feasibility(activities, transitions, T, I, S_norm, S_out_norm)
        
        activitiesDict = {a: (sum([v[0] for v in T[a].values()]), \
                          S[a] * len(log.cases)) for a in activities}
        transitionsDict = dict()
        for t in transitions:
            try: transitionsDict[tuple(t)] = T[t[0]][t[1]]
            except: transitionsDict[tuple(t)] = (0,0) # "imaginary" edges
        
        self.nodes = activitiesDict
        self.edges = transitionsDict

    def optimize(self, log, T, lambd, step, verbose=False):
        """Find optimal rates for the process model in terms of
        completeness and comprehension via quality function
        optimization.
        
        Parameters
        ----------
        log: Log
            Ordered records of events
        T: TransitionMatrix
            A matrix describing the transitions of a Markov chain
        lambd: float
            Regularization term coefficient: the more it is, the
            more penalty for the model complexity is
        step: int / float / list
            Step value or list of grid points for the search space

        Returns
        =======
        dict: optimal activities and paths rates

        See Also
        ---------
        Log
        TransitionMatrix
        """
        transitions_cnt = len([1 for i in log.flat_log \
                                 for j in log.flat_log[i]]) \
                          + len(log.flat_log.keys())

        def Q(theta1, theta2, lambd):
            """Quality (cost) function (losses + regularization term).
            The losses are defined by fitness function (see fitness) 
            and the regularization term is the average degree of a 
            directed graph.
            """
            self.update(log, theta1, theta2, T)
            n, m = len(self.nodes), len(self.edges)
            losses = self.fitness(log, T.T)
            
            return (1/lambd)*losses/transitions_cnt + lambd * m/n
        
        Q_val = dict() 
        per_done = 0
        if type(step) in [int, float]:
            per_step = 100 / (100//step + 1)**2
            grid = range(0,101,step)
        else: 
            per_step = 100 / len(step)
            grid = step

        for a in grid:
            for p in grid:
                Q_val[(a,p)] = Q(a, p, lambd)
                if not verbose: continue
                per_done += per_step
                sys.stdout.write("\rOptimization ..... {0:.2f}%".\
                                                format(per_done))
                sys.stdout.flush()
            if (p != 100) & (type(grid) == range): 
                Q_val[(a,100)] = Q(a, 100, lambd)
        if (a != 100) & (type(grid) == range): 
            Q_val[(100,100)] = Q(100, 100, lambd)
        print()
        Q_opt = min(Q_val, key=lambda theta: Q_val[theta])
        self.update(log, Q_opt[0], Q_opt[1], T)

        return {'activities': Q_opt[0], 'paths': Q_opt[1]}

    def aggregate(self, log, activity_rate, path_rate,
                    agg_type='outer', heuristic='all',
                    pre_traverse=False, ordered=False):
        """Aggregate cycle nodes into meta state, if it is 
        significant one. Note: the log is not changed.

        See also
        --------
        find_states
        reconstruct_log
        redirect_edges
        """
        SC = self.find_states(log, pre_traverse, ordered)
        if (agg_type == 'outer') | (agg_type == 'combine'):
            log_agg = Log()
            log_agg.flat_log = reconstruct_log(log, SC, ordered)
            log_agg.activities = log.activities.union(set(SC))
            log_agg.cases = log.cases
            T = TransitionMatrix()
            T.update(log_agg.flat_log)
            self.update(log_agg, activity_rate, path_rate, T)
        if (agg_type == 'inner') | (agg_type == 'combine'):
            if agg_type == 'combine':
                SC = [sc for sc in SC if sc in self.nodes] # only work with existing meta-states
            self.nodes, self.edges = redirect_edges(self.nodes,
                                                    self.edges,
                                                    meta_states=SC,
                                                    agg_type=agg_type,
                                                    heuristic=heuristic)

    def cycles_search(self, pre_traverse=False):
        """Perform DFS for cycles search in a graph (process model).
        Return list of cycles found in the graph.
        """
        G = incidence_matrix(self.edges)
        nodes =  ['start', 'end'] + list(self.nodes)
        cycles = []
        stack = []
        res = []
        
        visited = dict.fromkeys(nodes, False)
        def preorder_traversal(start_node):
            """Define the order of nodes traverse starting
            from the initial node ('start') of a process model.
            """
            visited[start_node] = True
            res.append(start_node)
            try: successors = G[start_node]
            except: successors = []
            for successor in successors:
                if not visited[successor]:
                    preorder_traversal(successor)
        
        if pre_traverse:
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

    def cycles_replay(self, log, cycles=[], ordered=False):
        """Replay log and count occurrences of cycles found
        in the process model.
        
        Parameters
        ----------
        log: Log
            Ordered records of events to replay
        cycles: list
            List of cycles to count occurrences via log replay
        ordered: bool
            If True, the order of cycle activities is fixed
            strictly (default False)
        
        Returns
        =======
        dict: with cycle (tuple) as a key and its occurrence 
            frequency in the log as a value
        
        See Also
        --------
        cycles_search
        """
        if not cycles:
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
                    if ordered:
                        cond = (tmp == c)
                    else: cond = (tmp in cycles_seq[c])
                    if cond:
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

    def find_states(self, log, ordered=False, pre_traverse=False):
        """Define meta states, i.e. significant cycles, in the model.
        A cycle found in the model is significant, if it occurs more
        than in a half of cases in the log.
        
        Parameters
        ----------
        log: Log
            Ordered records of events to replay
        ordered: bool
            If True, the order of cycle activities is fixed
            strictly (default False)
        pre_traverse: bool
            If True, performs graph traversal from 'start' node
            to define the order of activities in the cycles
            (default False)

        Returns
        =======
        list: of significant cycles (meta states)

        See also
        --------
        cycles_search
        cycles_replay
        """
        case_cnt = len(log.cases)
        cycles = self.cycles_search(pre_traverse)
        cycles = self.cycles_replay(log, cycles, ordered)
        SC = [] # significant cycles
        # Filtration
        for c in cycles:
            if len(c) == 1: continue
            if (cycles[c][1] / case_cnt >= 0.5):
                SC.append(c)
        return SC

    def fitness(self, log, T=None):
        """Return the value of a cost function that includes
        only loss term.
        """
        if T == None:
            TM = TransitionMatrix()
            TM.update(log)
            T = TM.T
        ADS = ADS_matrix(log, T)
        
        case_cnt = len(log.cases)
        eps = 10**(-len(str(case_cnt)))

        def loss(a_i, a_j):
            """Perform the loss function for log replay.
            The biggest penalty is for the absence of 
            transition in the model, if this transition
            always presences in the log.

            See also
            --------
            ADS_matrix
            """
            loss = 0
            if ADS[a_i][a_j] == 'A':
                loss = 1
            elif ADS[a_i][a_j] == 'S':
                loss = T[a_i][a_j][1] / case_cnt
            else:
                loss = eps
            return loss

        losses = 0
        for trace in log.flat_log:
            losses += loss('start', log.flat_log[trace][0])
            for i in range(len(log.flat_log[trace])-1):
                a_i = log.flat_log[trace][i]
                a_j = log.flat_log[trace][i+1]
                if (a_i,a_j) not in self.edges:
                    losses += loss(a_i, a_j)
            losses += loss(log.flat_log[trace][-1], 'end')
        for edge in self.edges:
            losses += loss(edge[0], edge[1])
        return losses
