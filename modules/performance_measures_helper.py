#!/usr/bin/env python3
import pandas as pd
import numpy as np

scalers = {
    "daily": 252,
    "monthly": 12,
    "weekly": 50,
    "biweekly": 25
}

""" 
Performance Measures Related Functions
"""
#Sharpe Ratio Functions
def sharpe_ratio(y, freq="daily"):
    """
    Classical Sharpe Ratio. Annualized Ratio
    """    
    # Annualized ratio
    return np.sqrt(scalers[freq]) * (y.mean() / y.std()) 

#Skewness Kurtosis Ratio
def sk_ratio(y):
    """
    Watanabe unscaled Ratio
    """        
    return (y.skew() / y.kurt()) 

# Modifiers for Rankers (Heuristic or Learned)
def israelsen_sharpe_ratio(y, freq="daily"):    
    """
    Israelsen Trick for the Sharpe Ratio
    """
    if y.mean()<0:
        return np.power(scalers[freq],1.5) *(y.mean()*y.std())
    else:
        return sharpe_ratio(y)

# Modifiers for Rankers (Heuristic or Learned)
def leon_sk_ratio(y):    
    """
    Leon Trick for the Skewness-Kurtosis Ratio
    """
    if y.skew()<0:
        return y.skew()*y.kurt()
    else:
        return sk_ratio(y)

#Quantile Related 
#VaR Ratio
def var_ratio(y, quant=0.05):
    return y.quantile(q=1-quant)/y.quantile(q=quant)

""" 
Functions for Compouding Returns
"""
def multi_period_return(period_returns):
    return np.prod(period_returns + 1) - 1

def net_cumreturn(data, last_row=False):
    """Net Cumulative Returns
    """
    df = ((1+data).cumprod(axis=0)-1)
    if last_row:
        return df.iloc[-1]
    return df

""" 
Scoring Related Functions
"""
def scorer(data, bins=20):
    """ Simple Scorer (The Higher, the Better) """
    df = pd.cut(x=data, bins=bins, labels=False)
    return df

def main():
    pass

if __name__ == "__main__":
    main()