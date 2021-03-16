<img src="/meta/logo.png" width="375" height="86,75">

## Table of contents
* [General info](#general-info)
* [Setup](#setup)
* [Features](#features)
* [Status](#status)
* [References](#references)

## General info
> Process mining module for Python.

*Process mining* is an emerging discipline that has been developing for the last two decades. It is a promising approach for the analysis and improving of intraorganizational workflows. Process mining has several types of techniques: *process discovery*, *conformance checking*, and *process enhancement*. With process discovery techniques, one can automatically construct a process model from routinely recorded data, an *event log*. Conformance checking aims to evaluate model compliance with data. After analysis of the real process executions, its enhancement can be proposed.

There is a plenty of commercial and open-source software for process mining, but how to use knowledge such tools extract from a log? In most cases, it could be performed only by visual assessment of a process model or via its statistics, and it would be desirable to extract knowledge *from* discovered processes. The derived data or formal structure (model) describing the process could be used, e.g., in modelling. This is the main motivation for the ProFIT development which provides such an opportunity, to look behind process discovery results. Future work encompasses all three steps in process mining. 

## Setup
You can clone this repository with the `git clone` command on a local machine and add a directory with the package to PATH. To start work with ProFIT, you should import `ProcessMap` from the `profit` module.

See the details of how to use it in [demo jupyter notebook](https://github.com/Siella/ProFIT/blob/master/demo/profit_examples_eng.ipynb).

**Required packages**:
* `Pandas`
* `Graphviz`
* `PM4Py`

(See [requirements](https://github.com/Siella/ProFIT/blob/master/meta/requirements.txt))

## Features
Process model discovered by ProFIT is a directly-follows graph (see figure below) with activities represented in nodes and their precendence relations as edges. The green node indicates the beginning of the process and shows the total number of cases presenting in the log, and the red node is related to the end of the process. The internal nodes and edges of the graph show the absolute frequencies of events and transitions, respectively: the more absolute value is, the darker or thicker element is.
![Process model example](/meta/process.png)

The discovery algorithm includes the basics of *Fuzzy Miner*, and as known, its properties do not guarantee a reachable graph which is desired to see the complete behaviors of the process. So, we perform depth-first search on the graph two times to check whether each node is a descendant of the initial state (“start”) and an ancestor of the terminal state (“end”) of the process model. This way, the model adjusted represents an executable process.

One can change process model details by tuning activities and paths rates: from the simplest to complex and fullness one. To achieve more automated way of complexity control, we defined the problem of discovering an optimal process model. In this optimization problem, an objective function includes complexity and loss terms. Regularization factor controls the trade-off between human comprehension of the process model and algorithm performance of log behaviours capturing. Thus, one can discover a process model by defining appropriate balance between its complexity and completeness.

We also introduced an approach for process model aggregation and abstraction (and possible simplification) via *meta-states* search. The idea originated from the healthcare domain, where a patient is involved in the processes. Still, it is broadly considered as an extension of a process discovery technique. Cycle nodes comprise a meta-state, if probability of cycle occurrence in the log exceeds specified threshold.

**List of main features ready**:
- [x] Model complexity / completeness control via `set_rates()` method (`activities`: int [0,100], `paths`: int [0,100]);
- [x] Optimized process model discovering via `set_params()` method (`optimize`: bool);
- [x] Process model simplification by nodes aggregation via `set_params()` method (`aggregate`: bool).

**To-do list**:
- [ ] Consider length-2(*k*)-relationship in log;
- [ ] Perform unit-tests;
- [x] Use results in predictive modeling.

## Status
This project is an ongoing research work, but you can try it already!

<img src="/meta/cat_logo.jpg" width="600" height="450">

## References
1. Van der Aalst, W. M. (2016). Process mining: Data science in action. Springer, Berlin, Heidelberg.
2. Ferreira, D. R. (2017). A primer on process mining. Springer, Cham.
3. Günther, C. W., & Van Der Aalst, W. M. (2007, September). Fuzzy mining–adaptive process simplification based on multi-perspective metrics. In International conference on business process management (pp. 328-343). Springer, Berlin, Heidelberg.
