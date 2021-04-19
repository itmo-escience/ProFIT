import ast
import os
import sys
import unittest

# Package import
PATH = os.getcwd()[:os.getcwd().rfind('\\')]  # path to directory - will vary when launching from console and file
sys.path.append(PATH)
sys.path.append(PATH+'\\profit')  # both required because of different start locations
sys.path.append(PATH+'\\ProFIT\\profit')  # This one is for console, previous - for current main

from profit.transition_matrix import TransitionMatrix
from profit.log import Log


class TransitionMatrixTest(unittest.TestCase):

    def setUp(self):
        monitoring = os.path.dirname(__file__) + '\\test_logs\\remote_monitoring.csv'
        self.log = Log()
        self.log.update(FILE_PATH=monitoring, cols=(0, 1), encoding='cp1251')
        self.tm = TransitionMatrix()

    def test_update(self):
        with open(os.path.dirname(__file__) + '\\test_results\\transition_matrix_test_update.txt',
                  encoding='utf-8') as file:
            expected = ast.literal_eval(file.read())
        self.tm.update(self.log.flat_log)
        result = self.tm.T
        self.assertEqual(expected, result)
