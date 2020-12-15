from log import Log
from transition_matrix import TransitionMatrix
from observer_abc import Observer
from util_pm import *
from util_agg import *
import sys
import math

class Graph(Observer):
    """Class to represent process model as a graph structure."""

    def __init__(self):
        """Graph object as a set of nodes (default None) and 
        a set of edges (default None).
        """
        self.nodes = None
        self.edges = None

    def update(self, log, activity_rate, path_rate, T, S_node=None):
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
        T: TransitionMatrix / dict
            A matrix describing the transitions of a Markov chain
            (Note: dictionary is passed when aggregation is performed)
        S_node: dict
            Node significance. Used only for aggregation type 'inner'
            (default None)

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
        S = S_node if S_node else node_significance(log)
        S_norm = dict_normalization(S, nested=False)
        activities = [a for a in S_norm if S_norm[a] >= (1 - activity_rate / 100)]
        
        # 2. Edge filtering
        T = T if type(T)==dict else transit_matrix(log, T.T)
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
        # Early algorithm stop
        if path_rate == 100:
            transitions = [(a_i, a_j) for a_i in T for a_j in T[a_i] \
                           if (a_i in activities + ['start', 'end']) \
                           & (a_j in activities + ['start', 'end'])]
        else:
            co = 1 - path_rate / 100 # cut-off threshold
            transitions = list(conflict_resolution(rS)) # initial set of transitions to preserve    
            transitions = edge_filtering(S_in_norm, transitions, co=co, type_='in')
            transitions = edge_filtering(S_out_norm, transitions, co=co, type_='out')
            for a_i in S_loop_norm:
                if (S_loop_norm[a_i] - 0.01 >= co) | (co == 0):
                    transitions.append((a_i, a_i))
        
        # 3. Check graph connectivity
        I = incidence_matrix(transitions) # Filtered incidence matrix
        check_feasibility(activities, transitions, T, I, S_norm, S_out_norm)
        
        activitiesDict = {a: (sum([v[0] for v in T[a].values()]),
                              int(S[a] * len(log.cases))) for a in activities}
        transitionsDict = dict()
        for t in transitions:
            try: transitionsDict[tuple(t)] = T[t[0]][t[1]]
            except: transitionsDict[tuple(t)] = (0, 0)  # "imaginary" edges
        
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
        transitions_cnt = len([1 for i in log.flat_log
                                 for j in log.flat_log[i]]) \
                          + len(log.flat_log.keys())
        ADS = ADS_matrix(log, T.T)
        N = len(log.activities)
        M = len([1 for a in T.T for b in T.T[a] if (a != 'start') & (b != 'end')])

        def Q(theta1, theta2, lambd):
            """Quality (cost) function (losses + regularization term).
            The losses are defined by fitness function (see fitness) 
            and the regularization term is the average degree of a 
            directed graph.
            """
            self.update(log, theta1, theta2, T)
            n, m = len(self.nodes)+2, len(self.edges)
            losses = self.fitness(log, T.T, ADS)
            # Calculate average degree
            compl = m / n
            # # # Calculate entropy
            # x_0 = m/(n*n)
            # x_1 = 1 - x_0
            # compl = -x_0 * math.log(x_0, 2) - x_1 * math.log(x_1, 2)
            # # Calculate elements ratio
            # edges = [e for e in self.edges if (e[0] != 'start') & (e[1] != 'end')]
            # nodes = {v for e in edges for v in e}
            # compl = 0.5 * (len(nodes)/N + len(edges)/M)
            # # # Calculate complete graph ratio
            # edges = [e for e in self.edges if (e[0] != e[1])]
            # nodes = {v for e in edges for v in e}
            # compl = len(edges)/(len(nodes)*(len(nodes)-1))
            
            return losses, compl
        
        Q_val = dict() 
        per_done = 0
        if type(step) in [int, float]:
            per_step = 100 / (100 // step + 1) ** 2
            grid = range(0, 101, step)
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
        max_loss = Q(0, 0, lambd)[0]
        max_compl = Q(100, 100, lambd)[1]
        for theta in Q_val:
            Q_val[theta] = (1 - lambd) * Q_val[theta][0] / max_loss + \
                           lambd * Q_val[theta][1] / max_compl
        Q_opt = min(Q_val, key=lambda theta: Q_val[theta])
        self.update(log, Q_opt[0], Q_opt[1], T)

        return {'activities': Q_opt[0], 'paths': Q_opt[1]}

    def aggregate(self, log, activity_rate, path_rate, agg_type='outer',
                  heuristic='all', pre_traverse=False, ordered=False, cycle_rel=0.5):
        """Aggregate cycle nodes into meta state, if it is 
        significant one. Note: the log is not changed.

        See also
        --------
        find_states
        reconstruct_log
        redirect_edges
        """
        SC = self.find_states(log, pre_traverse, ordered, cycle_rel)
        log_agg = Log()
        log_agg.flat_log = reconstruct_log(log, SC, ordered)
        log_agg.activities = log.activities.union(set(SC))
        log_agg.cases = log.cases
        T = TransitionMatrix()
        T.update(log_agg.flat_log)
        if agg_type not in ['outer', 'inner']:
            raise ValueError('Invalid aggregation type')
        if heuristic not in ['all', 'frequent']:
            raise ValueError('Invalid heuristic')
        if agg_type == 'inner':
            self.update(log_agg, 100, 0, T)
            nodes = self.nodes
            S = node_significance_filtered(log_agg, T.T, nodes, SC, heuristic)
            T_ = transit_matrix(log_agg, T.T)
            T1 = T_filtered(log_agg, T_, nodes, SC, heuristic=heuristic)
            log_agg.flat_log, log_agg.activities = filter_connections(log_agg, SC) 
            self.update(log_agg, activity_rate, path_rate, T1, S)
            self.nodes = add_frq(self.nodes, nodes, SC, T.T, heuristic)
        else:
            self.update(log_agg, activity_rate, path_rate, T)

    def find_nodes_order(self):
        """Perform traverse of a process model from start node.
        Return list of nodes ordered by their closeness to start.
        """
        G = incidence_matrix(self.edges)
        nodes = ['start', 'end'] + list(self.nodes)
        ordered_nodes = []
        visited = dict.fromkeys(nodes, False)

        def preorder_traversal(start_node):
            """ Define the order of nodes traverse starting
            from the initial node ('start') of a process model.
            """
            visited[start_node] = True
            ordered_nodes.append(start_node)
            try: successors = G[start_node]
            except: successors = []
            for successor in successors:
                if not visited[successor]:
                    preorder_traversal(successor)

        preorder_traversal('start')
        return ordered_nodes

    def find_cycles(self, log, pre_traverse=False, ordered=False):
        """Search cycles in log and count their occurrences.

        Parameters
        ----------
        log: Log
            Ordered records of events to replay
        pre_traverse: bool
            If True, performs graph traversal from 'start' node to define
            the order of activities in the cycles (default False)
        ordered: bool
            If True, the order of cycle activities is fixed strictly (default False)
        Returns
        =======
        dict: with cycle (tuple) as a key and its occurrence
            frequency in the log as a value
        """
        def check_edges(bad_edges_inds, s_ind, f_ind):
            for ind in bad_edges_inds:
                if ind >= f_ind:
                    return True
                elif s_ind <= ind:
                    return False
            return True

        cycles = dict()
        for case_log in log.flat_log.values():
            bad_edges = [i for i, e in enumerate(zip(case_log, case_log[1:]))
                         if e not in self.edges]

            case_cycles = set()
            for node in self.nodes:
                case_indices = [i for i, e in enumerate(case_log) if e == node]

                for s_i, f_i in zip(case_indices, case_indices[1:]):
                    cycle = case_log[s_i:f_i]

                    if f_i - s_i == len(set(cycle)) and check_edges(bad_edges, s_i, f_i):

                        if cycle not in cycles:
                            cycles[cycle] = [1, 0]
                        else:
                            cycles[cycle][0] += 1

                        if cycle not in case_cycles:
                            cycles[cycle][1] += 1
                            case_cycles.add(cycle)

        if pre_traverse:
            ordered_nodes = self.find_nodes_order()

        if not ordered:
            sum_cycles = dict()
            left = set()
            for cycle in cycles:
                if cycle not in left:
                    cycle_seq = [cycle[i:len(cycle)] + cycle[0:i]
                                 for i in range(len(cycle))]
                    if pre_traverse:
                        cycle_seq = {c: ordered_nodes.index(c[0]) for c in cycle_seq}
                        cycle = min(cycle_seq, key=cycle_seq.get)

                    sum_cycles[cycle] = [sum(cycles[c][i] for c in cycle_seq if c in cycles)
                                         for i in range(2)]
                    for c in cycle_seq:
                        left.add(c)

            cycles = sum_cycles

        return cycles

    def find_states(self, log, pre_traverse=False, ordered=False, cycle_rel=0.5):
        """Define meta states, i.e. significant cycles, in the model.
        A cycle found in the model is significant, if it occurs more
        than in cycle_rel of cases in the log.
        
        Parameters
        ----------
        log: Log
            Ordered records of events to replay
        pre_traverse: bool
            If True, performs graph traversal from 'start' node to define
            the order of activities in the cycles (default False)
        ordered: bool
            If True, the order of cycle activities is fixed strictly (default False)
        cycle_rel: float
            Significance level for meta states (default 0.5)
        Returns
        =======
        list: of significant cycles (meta states)

        See also
        --------
        find_cycles
        """
        cycles = self.find_cycles(log, pre_traverse, ordered)

        case_cnt = len(log.cases)
        return [c for c, (abs_freq, case_freq) in cycles.items()
                if len(c) > 1 and case_freq / case_cnt >= cycle_rel]

    def fitness(self, log, T=None, ADS=None):
        """Return the value of a cost function that includes
        only loss term.
        """
        if T is None:
            TM = TransitionMatrix()
            TM.update(log)
            T = TM.T
        if ADS is None:
            ADS = ADS_matrix(log, T)
        
        case_cnt = len(log.cases)
        eps = 10 ** (-len(str(case_cnt)))

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

        edges = self.edges
        edges1 = []
        for e in edges:
            if (type(e[0]) == tuple) & (type(e[1]) == tuple):
                for e_i in e[0]:
                    for e_j in e[1]:
                        edges1.append((e_i,e_j))
                edges1 += [(e[0][i], e[0][i+1]) for i in range(len(e[0]) - 1)]
                edges1 += [(e[1][i], e[1][i+1]) for i in range(len(e[1]) - 1)]
                edges1 += [(e[0][-1], e[0][0]), (e[1][-1], e[1][0])]
            elif type(e[0]) == tuple:
                for e_i in e[0]:
                    edges1.append((e_i,e[1]))
                edges1 += [(e[0][i], e[0][i+1]) for i in range(len(e[0]) - 1)]
                edges1 += [(e[0][-1], e[0][0])]
            elif type(e[1]) == tuple:
                for e_j in e[1]:
                    edges1.append((e[0], e_j))
                edges1 += [(e[1][i], e[1][i+1]) for i in range(len(e[1]) - 1)]
                edges1 += [(e[1][-1], e[1][0])]
            else:
                edges1.append(e)
        edges1 = set(edges1)

        losses = 0
        for log_trace in log.flat_log.values():
            losses += loss('start', log_trace[0])
            for a_i, a_j in zip(log_trace, log_trace[1:]):
                if (a_i, a_j) not in edges1:
                    losses += loss(a_i, a_j)
            losses += loss(log_trace[-1], 'end')
        for edge in edges1:
            losses += loss(edge[0], edge[1])
        return losses
