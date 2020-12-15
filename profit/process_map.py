from log import Log
from transition_matrix import TransitionMatrix
from graph import Graph
from renderer import Renderer

class ProcessMap:
    """Class to perform a process model from event log.

        Attributes
        ----------
        Log: Log
            Ordered records of events
        Rates: dict
            Dictionary of values for the process model
            simplification
        Params: dict
            Dictionary of parameters to regulate the 
            way of process model discovering and
            representation
        _Observers: dict
            Dictionary of "observers" that react to
            parameters/rates/data change

        See Also
        ---------
        Log
        Graph
        Updater
        Renderer
        TransitionMatrix
        
        Exampless
        --------
        >>> pm = ProcessMap()
        >>> pm.set_log("../PATH/LOG-FILE.csv", encoding='cp1251')
        >>> pm.set_rates(100, 0)
        >>> pm.set_params(optimize=False, aggregate=False)
        >>> pm.update()
        """

    def __init__(self):
        """Represent process model with default options.
            
            Settings
            ----------
            activities: float
                The inverse value to node significance threshold: the
                more it is, the more activities are observed in the model
                (default 100)
            paths: float
                The inverse value to edge significance threshold: the
                more it is, the more transitions are observed in the model
                (default 100)
            optimize: bool
                Find optimal rates for the process model (default True)
            aggregate: bool
                Aggregate activities into meta-states (default False)
            lambd: float
                Regularization factor of completeness and comprehension
                of the process model (default 0.5)
            step: int / float / list
                Step value or list of grid points for the search space
                (default 10)
            pre_traverse: bool
                If True, performs graph traversal from 'start' node
                to define the order of activities in meta states
                (default False)
            ordered: bool
                If True, the order of meta states activities is fixed
                strictly (default False)
            colored: bool
                Whether represent graph elements in color or in black
                and white (default True)
            verbose: bool
                If True, show optimization progress bar (default False)
            render_format: string
                Graphviz output format.
        """
        self.Log = Log()
        self.Rates = {'activities': 100, 'paths': 0}
        self.Params = {'optimize': True,
                       'lambd': 0.5,
                       'step': 10,
                       'verbose': False,
                       'aggregate': False,
                       'agg_type': 'outer',
                       'heuristic': 'all',
                       'pre_traverse': False,
                       'ordered' : False,
                       'cycle_rel': 0.5,
                       'colored': True,
                       'render_format': 'png'}
        self._Observers = {'T': TransitionMatrix(),
                           'Graph': Graph(),
                           'Renderer': Renderer()}

    def set_log(self, data=None, FILE_PATH='', cols=(0, 1), *args, **kwargs):
        """Set Log attribute of the class."""
        self.Log.update(data, FILE_PATH, cols=cols, *args, **kwargs)

    def set_rates(self, activity_rate, path_rate):
        """Set Rates attribute of the class."""
        if (activity_rate < 0) | (activity_rate > 100):
            raise ValueError('Activity rate is out of range')
        if (path_rate < 0) | (path_rate > 100):
            raise ValueError('Path rate is out of range')
        self.Rates = {'activities': activity_rate,
                      'paths': path_rate}

    def set_params(self, **kwargs):
        """Set Params attribute of the class."""

        def change_param(p):
            try: 
                self.Params[p] = kwargs[p]
            except:
                print(str(IOError) + ': No such parameter \'{}\'.'.format(p))
        
        for p in kwargs:
            change_param(p)

    def update(self):
        """Update "observers" and rates if settings were changed."""
        self._Observers['T'].update(self.Log.flat_log)

        if self.Params['optimize']:
            self.Rates = self._Observers['Graph'].optimize(self.Log,
                                                           self._Observers['T'],
                                                           self.Params['lambd'],
                                                           self.Params['step'],
                                                           self.Params['verbose'])
        else:
            self._Observers['Graph'].update(self.Log,
                                            self.Rates['activities'],
                                            self.Rates['paths'],
                                            self._Observers['T'])
        if self.Params['aggregate']:
            self._Observers['Graph'].aggregate(self.Log,
                                               self.Rates['activities'],
                                               self.Rates['paths'],
                                               self.Params['agg_type'],
                                               self.Params['heuristic'],
                                               self.Params['pre_traverse'],
                                               self.Params['ordered'],
                                               self.Params['cycle_rel'])

        self._Observers['Renderer'].update(self._Observers['T'],
                                           self._Observers['Graph'],
                                           self.Params['colored'])

    def get_log(self):
        """Return flat log (see Log)."""
        return self.Log.flat_log

    def get_rates(self):
        """Return activities and paths rates."""
        return self.Rates

    def get_params(self):
        """Return parameters of process model discovering."""
        return self.Params

    def get_T(self):
        """Return transition matrix (see TransitionMatrix)."""
        return self._Observers['T'].T

    def get_graph(self):
        """Return process model structure as a set of edges (see Graph)."""
        return self._Observers['Graph'].edges

    def render(self, save_path=None):
        """Return a graph object that can be rendered with the Graphviz 
        installation (see Renderer)."""
        if save_path:
            self._Observers['Renderer'].save(save_path)
        return self._Observers['Renderer'].GV
        
