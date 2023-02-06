#!/usr/bin/env python
# Assets Definitions (Move YAML definition file to a SQL Table)
import os
import yaml

import pandas as pd
import yfinance as yf

import mysql.connector as msql
from mysql.connector import Error

# Asset Loading (Y! Tickers or Definition Codes)
PYSCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = PYSCRIPT_PATH + "/config_server.yaml"

def config():
        with open(CONFIG_FILE,"r") as configfile:
            cfg=yaml.safe_load(configfile) 
                
        # parsing of yaml configuration file
        fx_codes = [codes for codes in cfg["fx"]]        
        # country code ISO4217 and/or Y! Tickers
        return {"codes": fx_codes, 
                "ticker": ["EUR"+code+"=X" for code in fx_codes]}
    
print(config()["codes"])

#Missing points:
"""
1. ETL (Extract from Y!, Transform pandas df, Load into SQL Server)
2. `crontab -e` for schedule daily batch execution on SQL MariaDB Linux Server 
(raspi4 arm64)
3. Expand YAML or SQL Table to a more extensive Universe of Assets
"""