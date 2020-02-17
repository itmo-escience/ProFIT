import os, sys
from util_func import *

def process_map(log, activity_rate, path_rate):
    """ Perform process model discovery and simplification.
    
    Returns a transition matrix as a dictionary and lists of
    nodes and edges filtrated.
    
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
    
    References
    ----------
    .. [1] Ferreira, D. R. (2017). A primer on process mining. Springer, Cham.
    .. [2] Günther, C. W., & Van Der Aalst, W. M. (2007, September). Fuzzy 
           mining–adaptive process simplification based on multi-perspective 
           metrics. In International conference on business process management 
           (pp. 328-343). Springer, Berlin, Heidelberg.
    
    Examples
    --------
    >>> log = Log("../PATH/LOG-FILE.csv")
    >>> pm = ProcessMap(log, 100, 5)
    """
    assert 0 <= activity_rate <= 100, "Activity rate is out of range (it should be from 0 to 100)"
    assert 0 <= path_rate <= 100, "Path rate is out of range (it should be from 0 to 100)"
    
    # 1. Node filtering
    S = node_significance(log)
    S_norm = dict_normalization(S, nested=False)
    activities = [a for a in S_norm if (S_norm[a] >= (100 - activity_rate) / 100)]
    
    # 2. Edge filtering
    T = transit_matrix(log)
    
    # Early algorithm stop
    if (path_rate == 100):
        transitions = [(a_i, a_j) for a_i in T for a_j in T[a_i] \
                       if (a_i in activities + ['start', 'end']) \
                       & (a_j in activities + ['start', 'end'])]
    else:
        # Significance matrix of outcoming edges
        S_out = edge_sig(T, source=activities+['start'], target=activities+['end'], type_='out')
        # Significance matrix of incoming edges (inverse outcoming)
        S_in = edge_sig(T, source=activities+['end'], target=activities+['start'], type_='in')
        # Self-loops case significance
        S_loop = {a_i: T[a_i][a_j][1] / len(log.cases) for a_i in T for a_j in T[a_i] \
                  if (a_i == a_j) & (a_i in activities)}
        # Evaluate the relative significance of conflicting relations
        rS = rel_sig(S_out, S_in)
        
        # Normalization
        S_out_norm = dict_normalization(S_out, nested=True)
        S_in_norm = dict_normalization(S_in, nested=True)
        S_loop_norm = dict_normalization(S_loop)
        
        co = (100 - path_rate) / 100 # cut-off threshold
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
        except: transitionsDict[tuple(t)] = (0,0)
    
    return T, activitiesDict, transitionsDict

def pm_optimized(log, lambd, step):
    """ Perform optimized process model discovery.
    
    Returns a transition matrix as a dictionary and lists of
    nodes and edges and a dictionary of the model's optimal rates.
    
    Parameters
    ----------
    log: Log
        Ordered records of events
    lambd: float
        Regularization coefficient of completeness and comprehension
        of process model
    step: int / float / list
        The step value or list of grid points for the search space
    
    See Also
    ---------
    process_map
    """
    assert type(step) in [int, float, list], \
    "Argument 'STEP' should be integer or float number or list of grid points"
    
    fl = log.flat_log
    activities = log.activities
    transits = [t for case_id in fl for t in zip(fl[case_id][:-1],fl[case_id][1:])]
    N, M = len(activities), len(set(transits))

    def Q(log, transits, N, M, theta1, theta2, lambd):
        # Quality function (losses + regularization) to optimize
        T, nodes, edges = process_map(log, theta1, theta2)
        case_cnt = sum([v[0] for v in T['start'].values()])
        eps = 10**(-len(str(case_cnt)))
        losses = 0
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
        
        def loss(a_i, a_j):
            loss = 0
            if ADS[a_i][a_j] == 'A':
                loss = 1
            elif ADS[a_i][a_j] == 'S':
                loss = T[a_i][a_j][1] / case_cnt
            else:
                loss = eps
            return loss

        for trace in log.flat_log:
            losses += loss('start', log.flat_log[trace][0])
            for i in range(len(log.flat_log[trace])-1):
                a_i = log.flat_log[trace][i]
                a_j = log.flat_log[trace][i+1]
                if (a_i,a_j) in edges:
                    continue
                else:
                    losses += loss(a_i, a_j)
            losses += loss(log.flat_log[trace][-1], 'end')

        n, m = len(nodes), len(edges) 
        
        return (1/lambd)*losses/len(transits) + lambd * m/n
    
    Q_val = dict()
    if type(step) in [int, float]:
        assert step > 0, "Argument 'STEP' should be greater than 0"
        per_done = 0
        per_step = 100 / (100//step + 1)**2
        for a in range(0,101,step):
            for p in range(0,101,step):
                Q_val[(a,p)] = Q(log, transits, N, M, a, p, lambd)
                per_done += per_step
                sys.stdout.write("\rOptimization ..... {0:.2f}%".format(per_done))
                sys.stdout.flush()
            if p != 100: Q_val[(a,100)] = Q(log, transits, N, M, a, 100, lambd)
        if a != 100: Q_val[(100,100)] = Q(log, transits, N, M, 100, 100, lambd)
    else:
        per_done = 0
        per_step = 100 / len(step)
        for a in step:
            for p in step:
                Q_val[(a,p)] = Q(log, transits, N, M, a, p, lambd)
                per_done += per_step
                sys.stdout.write("\rOptimization ..... {0:.2f}%".format(per_done))
                sys.stdout.flush()
    print()
    Q_opt = min(Q_val, key=lambda theta: Q_val[theta])
    T, nodes, edges = process_map(log, Q_opt[0], Q_opt[1])

    return T, nodes, edges, {'activities': Q_opt[0], 'paths': Q_opt[1]}
