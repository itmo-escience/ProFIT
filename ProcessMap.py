from Log import Log
from TransitionMatrix import TransitionMatrix
from Graph import Graph
from Renderer import Renderer

class ProcessMap():

    def __init__(self):
        self.Log = None
        self.Rates = {'activities': 100, 'paths': 0}
        self.Params = {'optimize': True, 'aggregate': False}
        self._Observers = {'T': None,
                           'Graph': None,
                           'Renderer': None}

    def set_log(self, FILE_PATH, c=(0,1), *args, **kwargs):
        log = Log(FILE_PATH, cols=c, *args, **kwargs)
        self.Log = log

    def set_rates(self, activity_rate, path_rate):
        if (activity_rate < 0) | (activity_rate > 100):
            raise ValueError('Activity rate is out of range')
        if (path_rate < 0) | (path_rate > 100):
            raise ValueError('Path rate is out of range')
        self.Rates = {'activities': activity_rate,
                      'paths': path_rate}

    def set_params(self, optimized, aggregated):
        self.Params = {'optimize': optimized,
                       'aggregate': aggregated}

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
                                    self._Observers['T'])
        else:
            G.update(self.Log,
                     self.Rates['activities'],
                     self.Rates['paths'],
                     self._Observers['T'])
        if self.Params['aggregate']:
            G.aggregate(self.Log,
                        self.Rates['activities'],
                        self.Rates['paths'],
                        self._Observers['T'])
        return G

    def render_map(self, save_path='', colored=True):
        R = Renderer()
        R.update(self._Observers['T'],
                 self._Observers['Graph'])
        return R

    def update(self):
        self._Observers['T'] = self.get_T()
        self._Observers['Graph'] = self.get_graph()
        self._Observers['Renderer'] = self.render_map()