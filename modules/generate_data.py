#!/usr/bin/env python3

import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import time
import re

BLACKROCK_CL_URL_ROOT = "https://www.blackrock.com/cl/productos/"

def index_components_finder(symbol="IVV", path = "data/pkl/"):
    """Scrapes BlackRock website public component time-series data for supported financial ETF products.
    Args:
        tickers : {‘IVV’, 'OEF', ‘IWB’, ‘IWM’, ‘IWV’}, default ‘IVV’ (S&P500)
        path : str, default './data/pkl'
    """
    
    etf_url = {        
        "IVV": "239726/ishares-core-sp-500-etf", # iShares Core S&P 500 ETF
        "OEF": "239723/ishares-core-sp-100-etf", # iShares Core S&P 500 ETF
        "IWB": "239707/ishares-russell-1000-etf", # iShares Russell 1000 ETF
        "IWM": "239710/ishares-russell-2000-etf", # iShares Russell 2000 ETF
        "IWV": "239714/ishares-russell-3000-etf", # iShares Russell 3000 ETF
    }

    url = BLACKROCK_CL_URL_ROOT + etf_url[symbol] + "#tabsAll"    
    # request page
    html = requests.get(url).content
    soup = BeautifulSoup(html)

    # find available dates
    holdings = soup.find("div", {"id": "holdings"})
    dates_div = holdings.find_all("div", "component-date-list")[1]
    dates_div.find_all("option")
    dates = [option.attrs["value"] for option in dates_div.find_all("option")]

    # download constituents for each date
    constituents = pd.Series(dtype=object)
    for date in dates:
        resp = requests.get(BLACKROCK_CL_URL_ROOT
        +etf_url[symbol]
        +f"/1506433277024.ajax?tab=all&fileType=json&asOfDate={date}").content[3:]
        tickers = json.loads(resp)
        tickers = [(arr[0], arr[1]) for arr in tickers['aaData']]
        date = datetime.strptime(date, "%Y%m%d")
        constituents[date] = tickers

    constituents = constituents.iloc[::-1] # reverse into cronlogical order
    
    # for pickle filename construction and saving (serial date)
    last_date = constituents.index[-1].strftime("%Y%m%d")
    pklfile_fullpath = path + symbol + "_historical_components_" + last_date + ".pkl"    
    constituents.to_pickle(pklfile_fullpath)
    return constituents

def change_ticker(ticker):
    rename_table = {
        "-": "LPRAX", # BlackRock LifePath Dynamic Retirement Fund
        "8686": "AFL", # AFLAC
        "4XS": "ESRX", # Express Scripts Holding Company 
        "AAZ": "APC", # Anadarko Petroleum Corporation
        "AG4": "AGN", # Allergan plc
        "BFB": "BF-B", # Brown-Forman Corporation
        "BF.B": "BF-B", # Brown-Forman Corporation
        "BF/B": "BF-B", # Brown-Forman Corporation
        "BF_B" : "BF-B", # Brown-Forman Corporation
        "BLD WI": "BLD", # TopBuild Corp.
        "BRKB": "BRK-B", # Berkshire Hathaway Inc.
        "BRK_B": "BRK-B", # Berkshire Hathaway Inc.
        "CC WI": "CC", # The Chemours Company
        "DC7": "DFS", # Discover Financial Services
        "DWDP": "DD", # Discover Financial Services
        "FB": "META",   # Facebook
        "GGQ7": "GOOG", # Alphabet Inc. Class C
        "GEC": "GE", # General Electric
        "HNZ": "KHC", # The Kraft Heinz Company
        "INCO": "INTC", # Intel
        "LOM": "LMT", # Lockheed Martin Corp.
        "LTD": "LB", # L Brands Inc.
        "LTR": "L", # Loews Corporation        
        "MPN": "MPC", # Marathon Petroleum Corp.
        "MYL": "VTRS", # Mylan NV (VIATRIS)
        "MWZ": "MET", # Metlife Inc.
        "MX4A": "CME", # CME Group Inc.
        "NCRA": "NWSA", # News Corporation
        "NTH": "NOC", # Northrop Grumman Crop.
        "PA9": "TRV", # The Travelers Companies, Inc.
        "QCI": "QCOM", # Qualcomm Inc.
        "RN7": "RF", # Regions Financial Corp
        "RTN" : "RTX", # Raytheon
        "SLBA": "SLB", # Schlumberger Limited
        "SYF-W": "SYF", # Synchrony Financial
        "SWG": "SCHW", # The Charles Schwab Corporation 
        "UAC/C": "UAA", # Under Armour Inc Class A
        "UBSFT": "UBSFY", # Ubisoft Entertainment
        "USX1": "X", # United States Steel Corporation
        "UUM": "UNM", # Unum Group
        "VISA": "V", # Visa Inc         
        "VIAC": "VIA", # viacom
        "WLTW": "WTW" # Willis Towers Watson                
    }
    if ticker in rename_table:
        fix = rename_table[ticker]
    else:
        fix = re.sub(r'[^A-Z]+', '', ticker)
    return fix

def all_times_stocks(financial_index, start_date, end_date):
    symbols = [change_ticker(elements[0]) for elements in financial_index[start_date:end_date][0]]
    all_symbols = symbols
    symbols = set(symbols)        

    for i, _ in enumerate(financial_index[start_date:end_date]):
        if i>0:
            sym = [change_ticker(stocks[0]) for stocks in financial_index[start_date:end_date][i]]        
            all_symbols.extend(sym)
            symbols = symbols.intersection(set(sym))            
        else:
            continue
    return symbols, set(all_symbols)

def simple_surviving_stocks(financial_index):
    """Parse (and correct with change_ticker()) stock component and find out all-times surviving stocks
    """
    initial_constituents = [change_ticker(sym[0]) for sym in financial_index[0]]
    final_constituents = [change_ticker(sym[0]) for sym in financial_index[-1]]
    return set(initial_constituents).intersection(set(final_constituents))

def main():
    pass

if __name__ == "__main__":
    main()

