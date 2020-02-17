from Log import Log
from TransitionMatrix import TransitionMatrix
from Graph import Graph
from Renderer import Renderer
from Updater import Updater

class ProcessMap():

    def __init__(self):
        self.Log = None
        self.Rates = {'activities': 100, 'paths': 0}
        self.Params = {'optimize': True, 'aggregate': False}
        self.__Observers = {'T': None,
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
        self.__Observers = UPD.Observers

    def get_log(self):
        return self.Log

    def get_rates(self):
        return self.Rates

    def get_params(self):
        return self.Params

    def get_T(self):
        return self.__Observers['T']

    def get_graph(self):
        return self.__Observers['Graph']

    def render_map(self, save_path='', colored=True):
        return self.__Observers['Renderer']
