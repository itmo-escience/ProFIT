import ast
import os
import sys
import unittest

# Package import
PATH = os.getcwd()[:os.getcwd().rfind('\\')]  # path to directory - will vary when launching from console and file
sys.path.append(PATH)
sys.path.append(PATH+'\\profit')  # both required because of different start locations
sys.path.append(PATH+'\\ProFIT\\profit')  # This one is for console, previous - for current main

from profit.process_map import ProcessMap
from profit.graph import Graph


class GraphTest(unittest.TestCase):

    def setUp(self):
        monitoring = os.path.dirname(__file__) + '\\test_logs\\remote_monitoring.csv'
        self.pm = ProcessMap()
        self.pm.set_log(FILE_PATH=monitoring, encoding='cp1251')
        self.pm.set_rates(80, 5)
        self.pm._Observers['T'].update(self.pm.Log.flat_log)

        self.graph = Graph()
        self.graph.update(self.pm.Log, self.pm.Rates['activities'], self.pm.Rates['paths'], self.pm._Observers['T'])
        self.log = self.pm.Log

    # graph.update in setUp doesn't affect on this test, but this has to be considered before other tests
    def test_update(self):

        with open(os.path.dirname(__file__) + '\\test_results\\graph_test_update.txt', encoding='utf-8') as file:
            expected_nodes = ast.literal_eval(file.readline())
            expected_edges = ast.literal_eval(file.readline())

        rates = (80, 5)
        self.graph.update(self.log, self.pm.Rates['activities'], self.pm.Rates['paths'], self.pm._Observers['T'])

        with self.subTest('nodes'):
            result = self.graph.nodes
            self.assertEqual(expected_nodes, result)
        with self.subTest('edges'):
            result = self.graph.edges
            self.assertEqual(expected_edges, result)

    @unittest.skip("Order varies from run to run and can't be checked")
    def test_find_nodes_order(self):

        with open(os.path.dirname(__file__) + '\\test_results\\graph_test_find_nodes_order.txt', encoding='utf-8') \
                as file:
            expected = ast.literal_eval(file.read())

        result = self.graph.find_nodes_order()
        self.assertEqual(expected, result)

    def test_find_cycles(self):
        self.maxDiff = None

        with open(os.path.dirname(__file__) + '\\test_results\\graph_test_find_cycles.txt', encoding='utf-8') as file:
            expected = ast.literal_eval(file.readline())
            expected_ordered = ast.literal_eval(file.readline())
            expected_pre_traverse = ast.literal_eval(file.readline())

        with self.subTest('random'):
            result = self.graph.find_cycles(self.log, False, False)
            sorted_result = {tuple(sorted(c)): fr for c, fr in result.items()}  # Result with no order may vary
            sorted_expected = {tuple(sorted(c)): fr for c, fr in result.items()}
            self.assertEqual(sorted(sorted_expected), sorted(sorted_result))
        with self.subTest('ordered'):
            result = self.graph.find_cycles(self.log, False, True)
            self.assertEqual(expected_ordered, result)
        with self.subTest('pre_traverse'):
            result = self.graph.find_cycles(self.log, True, False)
            self.assertEqual(expected_pre_traverse, result)

    def test_find_states(self):

        with open(os.path.dirname(__file__) + '\\test_results\\graph_test_find_states.txt', encoding='utf-8') as file:
            expected = ast.literal_eval(file.readline())
            expected_ordered = ast.literal_eval(file.readline())
            expected_pre_traverse = ast.literal_eval(file.readline())

        with self.subTest('random'):
            result = self.graph.find_states(self.log, False, False, 0.5)
            sorted_result = [tuple(sorted(c)) for c in sorted(result, key=len)]  # Result with no order may vary
            sorted_expected = [tuple(sorted(c)) for c in sorted(expected, key=len)]
            self.assertEqual(sorted(sorted_expected), sorted(sorted_result))
        with self.subTest('ordered'):
            result = self.graph.find_states(self.log, False, True, 0.5)
            self.assertEqual(sorted(expected_ordered), sorted(result))  # Need to avoid sorted here
        with self.subTest('pre_traverse'):
            result = self.graph.find_states(self.log, True, False, 0.5)
            self.assertEqual(sorted(expected_pre_traverse), sorted(result))

    @unittest.skip("Not implemented")
    def test_aggregate(self):
        result = self.graph.aggregate(self.log, self.pm.Rates['activities'], self.pm.Rates['paths'],
                                      agg_type='outer', heuristic='all', pre_traverse=False, ordered=False,
                                      cycle_rel=0.5)

    @unittest.skip("Not implemented")
    def test_fitness(self):
        result = self.graph.fitness(self.log, T=None, ADS=None)
        result = self.graph.fitness(self.log, self.pm._Observers['T'], ADS=None)

    @unittest.skip("Not implemented")
    def test_optimize(self):
        result = self.graph.optimize(self.log, self.pm._Observers['T'], self.pm.Params['lambd'], self.pm.Params['step'])


if __name__ == '__main__':
    unittest.main()
