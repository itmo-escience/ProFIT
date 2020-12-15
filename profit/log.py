import pandas as pd
import pm4py

class Log(object):
    """Perform event log object from a log-file.
    
    Attributes
    ----------
    flat_log: dict
        Event log as a dictionary where the key is a case id
        and the value is a sequence of events
    cases: set
        Set of cases in the log
    activities: set
        Set of activities in the log
    
    Examples
    --------
    >>> log = Log("../PATH/LOG-FILE.csv", encoding='cp1251')
    """
    def __init__(self):
        """Class Constructor."""
        self.flat_log = dict()
        self.cases = set()
        self.activities = set()

    def read_xes(self, FILE_PATH):
        """Read XES file into DataFrame."""
        log = pm4py.read_xes(FILE_PATH)
        df = pd.DataFrame([], columns=['ID', 'Activity', 'TimeStamp'])
        trace_id, activity, timestamp  = [], [], []
        for i,events in enumerate(log):
            for e in events:
                trace_id.append(i)
                activity.append(e['concept:name'])
                timestamp.append(e['time:timestamp'])
        df['ID'] = trace_id
        df['Activity'] = activity
        df['TimeStamp'] = timestamp
        df = df.sort_values('TimeStamp').drop('TimeStamp', axis=1)

        return df

    def update(self, data=None, FILE_PATH='', cols=(0,1), *args, **kwargs):
        """Update attributes via file reading.
        
        Parameters
        ----------
        data: DataFrame
            Log-file as DataFrame
        FILE_PATH: str
            Path to the CSV/TXT/XES log-file (alternative to data)
        cols: tuple
            Columns in the log-file to use as case id and activity
            attributes, respectively (default (0,1))
        """
        if FILE_PATH:
            if FILE_PATH[-4:] == ".xes":
                log = self.read_xes(FILE_PATH)
            else:
                log = pd.read_csv(FILE_PATH, usecols=cols, *args, **kwargs)
        else:
            log = data.iloc[:, list(cols)]
        log.columns = ['case_id', 'activity']
        log.set_index('case_id', drop=True, inplace=True)
        self.flat_log = dict(log.activity.groupby(level=0).agg(tuple))
        self.cases = set(log.index)
        self.activities = set(log.activity)
