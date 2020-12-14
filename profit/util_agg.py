def reconstruct_log(log, meta_states, ordered=False):
    """Rebuild log according to meta states found in the model.
    If ordered=True, the order of meta state activities is fixed
    strictly.
    """
    meta_states.sort(key=len, reverse=True)
    states_events = {v for state in meta_states for v in state}
    states_seq = {s: [s[i:len(s)]+s[0:i] for i in range(len(s))] \
                                         for s in meta_states}
    new_log = dict()
    for case, case_log in log.flat_log.items():
        case_log1 = []
        aggregated = False
        i = 0
        while i < len(case_log) - 1:
            if case_log[i] in states_events:
                for s in meta_states:
                    try: tmp = case_log[i:i + len(s) + 1]
                    except: continue
                    if tmp[0] == tmp[-1]:
                        if ordered: cond = (tmp[:-1] == s)
                        else: cond = (tmp[:-1] in states_seq[s])
                        if cond:
                            case_log1.append(s)
                            i += len(s) - 1
                            aggregated = True
                            break
            if not aggregated:
                case_log1.append(case_log[i])
            i += 1
            aggregated = False
        new_log[case] = tuple(case_log1)
    
    return new_log

def check_dict_key(d, key, set_val):
    if key not in d:
        d[key] = set_val

def dict_event_states(meta_states, nodes):
    event_states = dict()
    for state in meta_states:
        for event in state:
            check_dict_key(event_states, event, dict())
            event_states[event][state] = nodes[state][0]
    return event_states

def node_significance_filtered(log, T, nodes, meta_states, heuristic='all'):
    """Return node significance, i.e. activities case frequencies."""
    event_states = dict_event_states(meta_states, nodes)
    caseF = dict()
    # if heuristic in ['all','frequent']:
    for a in log.activities:
        if a in event_states:
            for case_log in log.flat_log.values():
                if heuristic == 'all':
                    for state in event_states[a]:
                        if state not in case_log:
                            check_dict_key(caseF, state, 0)
                            caseF[state] += 1  # 1 / len(state)
                else:
                    state = max(event_states[a], key=event_states[a].get)
                    if state not in case_log:
                        check_dict_key(caseF, state, 0)
                        caseF[state] += 1  # 1 / len(state)
        else:
            check_dict_key(caseF, a, 0)
            for case_log in log.flat_log.values:
                if a in case_log: caseF[a] += 1
    # elif heuristic == 'best':
    #     for a in log.activities:
    #         for case_id in log.flat_log:
    #             for state in meta_states:
    #                 if state in log.flat_log[case_id]:
    #                     check_dict_key(caseF, state, 0)
    #                     caseF[state] += 1
    #                 else:
    #                     for a in state:
    #                         if a in T:
    #                             if state in T[a]:
    #                                 check_dict_key(caseF, state, 0)
    #                                 caseF[state] += 1 / len(state)
    #                         elif state in T:
    #                             if a in T[state]:
    #                                 check_dict_key(caseF, state, 0)
    #                                 caseF[state] += 1 / len(state)
    # Activities (node) significance
    S = {a: caseF[a] / len(log.cases) for a in caseF}
    return S

def T_filtered(log, T, nodes, meta_states, heuristic='all'):
    """Redirect edges and its frequencies."""
    Tf = dict()
    for a in T:
        Tf[a] = dict()
        for x in T[a]:
            Tf[a][x] = T[a][x]
    event_states =dict_event_states(meta_states, nodes)
    to_add, to_dec = dict(), dict()

    def check_add(a_i, a_j, reverse=False):
        if reverse: a_i, a_j = a_j, a_i
        check_dict_key(Tf[a_i], a_j, (0, 0))
        abs_frq, cse_frq = Tf[a_i][a_j]
        Tf[a_i][a_j] = (abs_frq + 1, cse_frq)
        check_dict_key(to_add, a_i, dict())
        check_dict_key(to_add[a_i], a_j, True)
        if to_add[a_i][a_j]:
            abs_frq, cse_frq = Tf[a_i][a_j]
            Tf[a_i][a_j] = (abs_frq, cse_frq + 1)
            to_add[a_i][a_j] = False

    def apply_heuristic_all(a_i, a_j, reverse=False):
        if a_i not in event_states[a_j]: 
            for state in event_states[a_j]:
                check_add(a_i, state, reverse=reverse)

    def apply_heuristic_frequent(a_i, a_j, reverse=False):
        state = max(event_states[a_j], key=event_states[a_j].get)
        if a_i != state:
            check_add(a_i, state, reverse=reverse)

    def apply_heuristic(a_i, a_j, reverse=False):
        if heuristic == 'all': 
            apply_heuristic_all(a_i, a_j, reverse=reverse)
        elif heuristic == 'frequent':
            apply_heuristic_frequent(a_i, a_j, reverse=reverse)

    for case_log in log.flat_log.values():
        case_log = ['start'] + list(case_log) + ['end']
        for a_i, a_k, a_j in zip(case_log, case_log[1:], case_log[2:]):
            if (a_k in event_states) & (a_i not in event_states):
                apply_heuristic(a_i, a_k, reverse=False)
            if (a_k in event_states) & (a_j not in event_states):
                apply_heuristic(a_j, a_k, reverse=True)
            if a_k in meta_states:
                check_dict_key(to_dec, a_i, dict())
                check_dict_key(to_dec[a_i], a_k, False)
                to_dec[a_i][a_k] = True
                check_dict_key(to_dec, a_k, dict())
                check_dict_key(to_dec[a_k], a_i, False)
                to_dec[a_k][a_i] = True

        for i in to_add:
            for j in to_add[i]:
                if i in to_dec and j in to_dec[i]:
                    if (not to_add[i][j]) & (to_dec[i][j]):
                        abs_frq, cse_frq = Tf[i][j]
                        Tf[i][j] = (abs_frq, cse_frq - 1)
                to_add[i][j] = True
        for i in to_dec:
            for j in to_dec[i]:
                to_dec[i][j] = False
    return Tf

def filter_connections(log, meta_states):
    """Exclude from log single events that presents in meta-states."""
    events_to_filtrate = {v for state in meta_states for v in state}
    new_log = {case: tuple(e for e in case_log if
                           e not in events_to_filtrate)
               for case, case_log in log.flat_log.items()}
    activities = [a for a in log.activities if a not in events_to_filtrate]
    return new_log, activities

def add_frq(nodes, nodes_to_add, meta_states, T, heuristic='all'):
    event_states = dict_event_states(meta_states, nodes_to_add)
    nodes1 = dict()
    for v, freq in nodes.items():
        if v in meta_states:
            nodes1[v] = (freq[0], freq[1], dict())
            for v_i in v:
                if v_i not in nodes1[v][2]:
                    nodes1[v][2][v_i] = freq[0]
                if heuristic == 'all':
                    if v_i in nodes_to_add:
                        nodes1[v][2][v_i] += nodes_to_add[v_i][0]
                elif heuristic == 'frequent':
                    if v == max(event_states[v_i], key=event_states[v_i].get):
                        nodes1[v][2][v_i] += nodes_to_add[v_i][0]
                # elif heuristic == 'best':
                #     if (v_i in T) & (v_i in nodes_to_add):
                #         if v in T[v_i]:
                #             nodes1[v][2][v_i] += nodes_to_add[v_i][0]
                #     elif v in T:
                #         if (v_i in T[v]) & (v_i in nodes_to_add):
                #             nodes1[v][2][v_i] += nodes_to_add[v_i][0]
        else:
            nodes1[v] = nodes_to_add[v]
    return nodes1
