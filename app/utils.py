import pandas as pd
from collections import deque

def load_data(filename):
    df = pd.read_csv(filename, sep=',')
    return df

def create_queue(data):
    d = deque()
    for i in range(len(data)):
        d.append(data[i])

    return d
