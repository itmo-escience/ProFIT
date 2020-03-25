# ProFIT: Process Flow Investigation Tool
> Process mining module for Python.

## Table of contents
* [General info](#general-info)
* [Setup](#setup)
* [Features](#features)
* [Status](#status)
* [References](#references)

## General info
*Process mining* is an emerging discipline that have been developing for less than twenty years. Despite that fact, process mining is a promising approach to get insights into the real execution of processes in different organizations. Process mining is aimed to extract knowledge from routinely recorded data, *event logs*, that include information about completeness status of process steps with associated data, such as activities, resources, start/end timestamps, etc. There is a plenty of commercial and open-source software for process mining, but how to use the knowledge such tools extract from a log? In most cases one can perform an assessment of a process model only visualy. However, it would be desirable to extract knowledge *from* discovered process as well as from the event log. It could be data or formal structure describing the process one might use, e.g., in modelling. This is the main motivation for the ProFIT development that provides such an opportunity.

## Setup
You can clone this repository with the `git clone` command on a local machine and add a directory with the package to PATH. To start work with the ProFIT, you should import `ProcessMap` from the `profit` module. See the details of how to use it in [demo jupyter notebook](https://github.com/Siella/ProFIT/blob/master/demo/profit_examples.ipynb).

## Features
Process model discovered by ProFIT is a state graph (see figure below) in the form of transition system like a finite state automation but with activities represented in nodes rather than in edges. The green node indicates the beginning of the process and shows the total number of cases presenting in the log, and the red node is related to the end of the process. The internal nodes and edges of the graph show the absolute frequencies of events and transitions, respectively: the more absolute value is, the darker or thicker element is. The proposed miner technique includes the basics of state-of-the-art *Fuzzy Miner*. However, the properties of Fuzzy nets (models produced by Fuzzy Miner) do not guarantee a reachable or even connected graph that is desired to see the complete behaviors of process traces. So, we perform depth-first search (DFS) on the state graph two times to check whether each node of the graph is a descendant of the initial state (“start”) and a parent of the terminal state (“end”) of the process. This way, the model adjusted represents an executable process.
![Process model example](/meta/process.png)
One can change process model detail by tuning activities and paths rates: from the simplest to complex and fullness one. But how to obtain the model automatically? To answer this question, we defined the problem of discovering an optimal process model. In this optimization problem, an objective function includes complexity and loss terms. Regularization parameter controls the balance between human comprehension and completeness of the process model, i.e. simplicity and complexity of the graph. Thus, one can discover process model optimized in one of the senses.
We also introduced an approach for process model simplification. Simplification of the process model can be done by aggregating nodes into meta-states. We assume cycle nodes to be a *meta-state*, if probability of cycle occurrence in the log exceeds specified threshold. This way one can distinguish most significant cyclic behavior, i.e. process stage, and exceptions.

**List of main features ready**:
- [x] Model complexity / completeness control via `set_params()` method (`activities`: int [0,100], `paths`: int [0,100]);
- [x] Optimized process model discovering via `set_params()` method (`optimize`: bool);
- [x] Process model simplification by nodes aggregation via `set_params` method (`aggregate`: bool).

**To-do list**:
- [] Consider length-2(*k*)-relationship in log;
- [] Perform unit-tests;
- [] Use results in predictive modeling.

## Status
Project is an ongoing research work.

## References
1. Ferreira, D. R. (2017). A primer on process mining. Springer, Cham.
2. Günther, C. W., & Van Der Aalst, W. M. (2007, September). Fuzzy mining–adaptive process simplification based on multi-perspective metrics. In International conference on business process management (pp. 328-343). Springer, Berlin, Heidelberg.