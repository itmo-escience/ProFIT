# Functionality
* Class `ProcessMap`
  - `set_log(self, FILE_PATH, cols=(0,1), *args, **kwargs)`: Set Log attribute of the class.
  - `set_rates(self, activity_rate, path_rate)`: Set Rates attribute of the class.
  - `set_params(self, **kwargs)`: Set Params attribute of the class.
  - `update(self)`: Update "observers" and rates if settings were changed.
  - `get_log(self)`: Return flat log.
  - `get_rates(self)`: Return activities and paths rates.
  - `get_params(self)`: Return parameters of process model discovering.
  - `get_T(self)`: Return transition matrix.
  - `get_graph(self)`: Return process model structure as a set of edges.
  - `render(self, save_path=None)`: Return a graph object that can be rendered with the Graphviz installation.
