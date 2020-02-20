from Log import Log
from TransitionMatrix import TransitionMatrix
from Graph import Graph
from Renderer import Renderer

class ProcessMap():

    def __init__(self):
        self.Log = None
        self.Rates = {'activities': 100, 'paths': 0}
        self.Params = {'optimize': True, 
                       'aggregate': False,
                       'lambd': 0.5,
                       'step': 10,
                       'pre_traverse': False,
                       'ordered' : False,
                       'colored': True}
        self._Observers = {'T': None,
                           'Graph': None,
                           'Renderer': None}

    def set_log(self, FILE_PATH, cols=(0,1), *args, **kwargs):
        log = Log(FILE_PATH, cols=cols, *args, **kwargs)
        self.Log = log

    def set_rates(self, activity_rate, path_rate):
        if (activity_rate < 0) | (activity_rate > 100):
            raise ValueError('Activity rate is out of range')
        if (path_rate < 0) | (path_rate > 100):
            raise ValueError('Path rate is out of range')
        self.Rates = {'activities': activity_rate,
                      'paths': path_rate}

    def set_params(self, **kwargs):
        def change_param(p):
            try: 
                self.Params[p] = kwargs[p]
            except:
                print(str(IOError) + \
                ': No such parameter \'{}\'.'.format(p))
        
        for p in kwargs:
            change_param(p)

    def update(self):
        UPD = Updater()
        UPD.Log = self.Log
        UPD.Rates = self.Rates
        UPD.Params = self.Params
        UPD.update()
        if self.Params['optimize']:
            self.Rates = UPD.Rates
        self._Observers = UPD._Observers

    def get_log(self):
        return self.Log

    def get_rates(self):
        return self.Rates

    def get_params(self):
        return self.Params

    def get_T(self):
        return self._Observers['T']

    def get_graph(self):
        return self._Observers['Graph']

    def render_map(self, save_path='', colored=True):
        return self._Observers['Renderer']


class Updater(ProcessMap):

    def get_T(self):
        T = TransitionMatrix()
        T.update(self.Log.flat_log)
        return T

    def get_graph(self):
        G = Graph()
        if self.Params['optimize']:
            self.Rates = G.optimize(self.Log,
                                    self._Observers['T'],
                                    self.Params['lambd'],
                                    self.Params['step'])
        else:
            G.update(self.Log,
                     self.Rates['activities'],
                     self.Rates['paths'],
                     self._Observers['T'])
        if self.Params['aggregate']:
            G.aggregate(self.Log,
                        self.Rates['activities'],
                        self.Rates['paths'],
                        self._Observers['T'],
                        self.Params['pre_traverse'],
                        self.Params['ordered'])
        return G

    def render_map(self):
        R = Renderer()
        R.update(self.Params['colored'],
                 self._Observers['T'],
                 self._Observers['Graph'])
        return R

    def update(self):
        self._Observers['T'] = self.get_T()
        self._Observers['Graph'] = self.get_graph()
        self._Observers['Renderer'] = self.render_map()