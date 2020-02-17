from Log import Log
from TransitionMatrix import TransitionMatrix
from Graph import Graph
from Renderer import Renderer

class Updater():

    def __init__(self):
        Log = None
        Rates = {'activities': 100, 'paths': 0}
        Params = {'optimize': True, 'aggregate': False}
        Observers = {'T': None,
                       'Graph': None,
                       'Renderer': None}

    def get_T(self):
        T = TransitionMatrix()
        T.update(self.Log.flat_log)
        return T

    def get_graph(self):
        G = Graph()
        if self.Params['optimize']:
            self.Rates = G.optimize(self.Log,
                                    self.Observers['T'])
        else:
            G.update(self.Log,
                     self.Rates['activities'],
                     self.Rates['paths'],
                     self.Observers['T'])
        if self.Params['aggregate']:
            G.aggregate(self.Log,
                        self.Rates['activities'],
                        self.Rates['paths'],
                        self.Observers['T'])
        return G

    def render_map(self, save_path='', colored=True):
        R = Renderer()
        R.update(self.Observers['T'],
                 self.Observers['Graph'])
        return R

    def update(self):
        self.Observers['T'] = self.get_T()
        self.Observers['Graph'] = self.get_graph()
        self.Observers['Renderer'] = self.render_map()