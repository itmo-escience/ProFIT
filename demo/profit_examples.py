import os, sys
import pandas as pd

# Package import
PATH = os.getcwd()[:os.getcwd().rfind('\\')] # path to ProFIT directory
sys.path.append(PATH)
sys.path.append(PATH+'\\profit')

from profit import ProcessMap

monitoring = PATH + "/demo/log_examples/remote_monitoring_eng.csv"
declarations = PATH + "/demo/log_examples/DomesticDeclarations.xes"

def main():
    if __name__== "__main__" :
        # Log example in csv
        df_monitoring = pd.read_csv(monitoring, encoding='cp1251')
        print(df_monitoring.head())

        # Init ProcessMap and set log in CSV/TXT/XES/pandas.DataFrame
        pm = ProcessMap()
        pm.set_log(FILE_PATH = monitoring, 
                   # data = df_monitoring,
                   encoding='cp1251')
        pm.set_rates(80, 5) # activity and path rates (should set optimize=False for this setting)
        pm.set_params(optimize=False, aggregate=False) # option to discover an optimal process model and its elements aggregation
        pm.update() # update method have to be called after each setting (or series)!
        pm.render(show_only=True, save_path=None) # pass a path to a directory where the result will be saved

main()