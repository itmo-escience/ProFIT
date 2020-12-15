from observer_abc import Observer

class TransitionMatrix(Observer):
    """Class to represent a transition matrix that 
    describes the transitions of a Markov chain.
    """

    def __init__(self):
        """"Transition matrix is represented in the T attribute
        (default empty dictionary).
        """
        self.T = dict()

    def update(self, log):
        """Transition matrix as dictionary indicating relations 
        between activities, i.e. their following each other in
        the log, and their absolute and case frequencies.
        """
        T = dict()
        to_add = dict()
        for log_trace in log.values():
            for a_i, a_j in zip(log_trace, log_trace[1:]):
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
