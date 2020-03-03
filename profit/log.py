import pandas as pd

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
    def __init__(self, FILE_PATH, cols=(0,1), *args, **kwargs):
        """Class Constructor.
        
        Parameters
        ----------
        FILE_PATH: str
            Path to the CSV log-file
        cols: tuple
            Columns in the log-file to use as case id and activity
            attributes, respectively (default (0,1))
        """
        log = pd.read_csv(FILE_PATH, usecols=cols, *args, **kwargs)
        log.columns = ['case_id', 'activity']
        log.set_index('case_id', drop=True, inplace=True)
        self.flat_log = dict(log.activity.groupby(level=0).agg(tuple))
        self.cases = set(log.index)
        self.activities = set(log.activity)