class TransitionMatrix():

    def __init__(self):
        self.T = dict()

    def update(self, log):
        T = dict()
        to_add = dict()
        for case_id in log:
            for i in range(len(log[case_id]) - 1):
                a_i = log[case_id][i]
                a_j = log[case_id][i+1]
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
        
        self.T = T