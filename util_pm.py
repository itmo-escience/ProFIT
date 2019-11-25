import os, sys
from util_func import *

def process_map(log, activity_rate, path_rate):
    assert 0 <= activity_rate <= 100, "Activity rate is out of range (it should be from 0 to 100)"
    assert 0 <= path_rate <= 100, "Path rate is out of range (it should be from 0 to 100)"
    
    # 1. Node filtering
    S = dict_normalization(node_significance(log), nested=False)
    activities = [a for a in S if (S[a] >= (100 - activity_rate) / 100)]
    
    # 2. Edge filtering
    T = transit_matrix(log)
    
    # Early algorithm stop
    if (path_rate == 100):
        transitions = [(a_i, a_j) for a_i in T for a_j in T[a_i] \
                       if (a_i in activities + ['start', 'end']) \
                       & (a_j in activities + ['start', 'end'])]
        return T, activities, transitions
    
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
    S_out = dict_normalization(S_out, nested=True)
    S_in = dict_normalization(S_in, nested=True)
    S_loop = dict_normalization(S_loop)
    
    co = (100 - path_rate) / 100 # cut-off threshold
    transitions = list(conflict_resolution(rS)) # initial set of transitions to preserve    
    transitions = edge_filtering(S_in, transitions, co=co, type_='in')
    transitions = edge_filtering(S_out, transitions, co=co, type_='out')
    for a_i in S_loop:
        if (S_loop[a_i] - 0.01 >= co) | (co == 0):
            transitions.append((a_i,a_i))
    
    # 3. Check graph connectivity
    I = incidence_matrix(transitions) # Filtered incidence matrix
    check_feasibility(activities, transitions, I, S, S_out)
    
    return T, activities, transitions

def pm_optimized(log, lambd, step):
    assert type(step) in [int, float, list], \
    "Argument 'STEP' should be integer or float number or list of grid points"
    
    def Q(log, transits, N, M, theta1, theta2, lambd):
        _, nodes, edges = process_map(log, theta1, theta2)
        edges = [e for e in edges if (e[0] != 'start') | (e[1] != 'end')]
        n, m = len(nodes), len(edges)
        losses = len([e for e in transits if e not in edges])
        
        return losses/len(transits) + .5 * lambd * (m/M + n/N)
    
    fl = log.flat_log
    activities = log.activities
    transits = [t for case_id in fl for t in zip(fl[case_id][:-1],fl[case_id][1:])]
    N, M = len(activities), len(set(transits))
    
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
