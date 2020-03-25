# Functionality
The main functionality is presented below. For more details see docstrings in an appropriate module.
* Class `ProcessMap`
  - `.set_log(self, FILE_PATH, cols=(0,1), *args, **kwargs)`: Set Log attribute of the class.
  - `.set_rates(self, activity_rate, path_rate)`: Set Rates attribute of the class.
  - `.set_params(self, **kwargs)`: Set Params attribute of the class.
  - `.update(self)`: Update "observers" and rates if settings were changed.
  - `.get_log(self)`: Return flat log.
  - `.get_rates(self)`: Return activities and paths rates.
  - `.get_params(self)`: Return parameters of process model discovering.
  - `.get_T(self)`: Return transition matrix.
  - `.get_graph(self)`: Return process model structure as a set of edges.
  - `.render(self, save_path=None)`: Return a graph object that can be rendered with the Graphviz installation.

* Class `Graph`
  - `.update(self, log, activity_rate, path_rate, T)`: Update nodes and edges attributes.
  - `.optimize(self, log, T, lambd, step, verbose=False)`: Find optimal rates for the process model.
  - `.aggregate(self, log, activity_rate, path_rate, pre_traverse=False, ordered=False)`: Aggregate cycle nodes into meta state.
  - `.cycles_search(self, pre_traverse=False)`: Perform DFS for cycles search in a graph.
  - `.cycles_replay(self, log, cycles=[], ordered=False)`: Replay log and count occurrences of cycles found in the process model.
  - `.find_states(self, log, ordered=False, pre_traverse=False)`: Define meta states in the model.
  - `.fitness(self, log, T=None)`: Return the value of a cost function that includes only loss term.

* Class `Renderer`
  - `.update(self, TM, G, colored=True)`: Update graph object and its representation.
  - `.show(self)`: Return graph in DOT language.
  - `.save(self, save_path=None)`: Render and save graph in PNG (GV) format in the working directory or in *save_path*.
