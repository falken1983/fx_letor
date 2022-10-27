#!/usr/bin/env python3
import pandas as pd
import numpy as np

def score_preprocessor(data, **kwargs):   
    
    scores_stacked = data.stack(dropna=False)
    scores = scores_stacked.to_numpy()
    rebalance_ids = scores_stacked.index.get_level_values("Date")
    rebalance_ids = rebalance_ids.strftime("%Y%m%d").to_numpy().astype(np.uint)
    stock_map = {i: stock for i,stock in enumerate(scores_stacked.index.get_level_values(1).unique())}
    return scores, rebalance_ids, stock_map

def feature_preprocessor(feature, **kwargs):
    return feature.stack(dropna=False).to_numpy()

"""Custom splitter
"""
def custom_split(*arrays, train_obs=36, val_obs=12):
    lst_array_train = []
    lst_array_val = []
    lst_array_test = []    
      
    for array in arrays:
        array_train = array[:int(train_obs*NSTOCKS_SHAPE_1)]
        array_val = array[int(train_obs*NSTOCKS_SHAPE_1):int((train_obs + val_obs)*NSTOCKS_SHAPE_1)]
        array_test = array[int((train_obs + val_obs)*NSTOCKS_SHAPE_1):]
        lst_array_train.append(array_train)
        lst_array_val.append(array_val)
        lst_array_test.append(array_test)
    return lst_array_train, lst_array_val, lst_array_test

def main():
    pass

if __name__ == "__main__":
    main()