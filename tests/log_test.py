import ast
import os
import sys
import unittest

# Package import
PATH = os.getcwd()[:os.getcwd().rfind('\\')]  # path to directory - will vary when launching from console and file
sys.path.append(PATH)
sys.path.append(PATH+'\\profit')  # both required because of different start locations
sys.path.append(PATH+'\\ProFIT\\profit')  # This one is for console, previous - for current main

from profit.log import Log


class TransitionMatrixTest(unittest.TestCase):

    def setUp(self):
        self.log = Log()

    def test_update(self):
        monitoring = os.path.dirname(__file__) + '\\test_logs\\remote_monitoring.csv'
        self.log.update(FILE_PATH=monitoring, cols=(0, 1), encoding='cp1251')

        with open(os.path.dirname(__file__) + '\\test_results\\log_test_update.txt', encoding='utf-8') as file:
            expected_flat_log = ast.literal_eval(file.readline())
            expected_cases = ast.literal_eval(file.readline())
            expected_activities = ast.literal_eval(file.readline())

        with self.subTest('flat_log'):
            result = self.log.flat_log
            self.assertEqual(expected_flat_log, result)
        with self.subTest('cases'):
            result = self.log.cases
            self.assertEqual(expected_cases, result)
        with self.subTest('expected_activities'):
            result = self.log.activities
            self.assertEqual(expected_activities, result)
