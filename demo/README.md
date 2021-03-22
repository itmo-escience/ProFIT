## Data description
ProFIT usage is demonstrated with two event logs:
1. [**Remote monitoring**](https://github.com/Siella/ProFIT/blob/master/demo/log_examples/remote_monitoring_eng.csv): data provided by [PMT Online](https://pmtonline.ru/) within a collaborative project. It contains events triggered by in-home blood pressure measurements made by patients suffering from arterial hypertension. There are several clinical and non-clinical events: red zone (exceeding critical levels), yellow zone (exceeding target levels), notifications about measurement missing, etc.
2. [**Reimbursement process**](https://github.com/Siella/ProFIT/blob/master/demo/log_examples/DomesticDeclarations.xes): data from BPI Challenge 2020 collected from the reimbursement process at Eindhoven University of Technology for 2017-2018. See data description on the [BPI Challenge website](https://icpmconference.org/2020/bpi-challenge/).

Additionaly, we upload two event logs for physician and nurse workflows in [Almazov center](http://www.almazovcentre.ru/?lang=en) in Saint Petersburg, one of the leading cardiological centers in Russia we collaborate. We used data from a hospital access control system and a healthcare information system to compose an event log of staff activities and logistics. These sophisticated processes are comprised of labs, procedures, branch communications, etc. Data need to be processed thoroughly, so we do not use these cases for demo now.

## Code examples

Init ProcessMap and fit data via `set_log` method.

```python
declarations = "../ProFIT/demo/log_examples/DomesticDeclarations.xes"
pm = ProcessMap()
pm.set_log(FILE_PATH = declarations)
pm.update() # may be called after series of settings
```

Model adjustment.
```python
pm.set_rates(80, 5) # activity and path rates (should set optimize=False for this setting)
# below are default parameters
pm.set_params(optimize=True, # option to discover an optimal process model
              lambd=0.5, # regularization factor for model complexity and completeness (increasing lambda results in a simpler model)
              step=10, # step size for grid search of an optimal model
              verbose=False, # print the progress of optimization
              aggregate=False, # option to aggregate nodes into meta-states (if there are)
              agg_type='outer', # type of aggregation (possible are 'inner' and 'outer')
              heuristic='all', # heuristic to use for element relations redirecting
              pre_traverse=False, # establish order of activities traversing a directed graph
              ordered=False, # whether the order of meta-state activities are strict
              cycle_rel=0.5, # significance threshold for cycles to compose meta-states
              colored=True, # black and white or colored process visualization
              render_format='png') # saving format (should be supported by Graphviz)
pm.update()
```

Visualize a result (for jupyter-notebook `show_only=False`).
```python
pm.render(show_only=True, save_path=None)
```
