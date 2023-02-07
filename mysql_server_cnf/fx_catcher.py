#!/usr/bin/env python
# Assets Definitions (Move YAML definition file to a SQL Table)
import os
import yaml
import json

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
# *Extract* from Y! EOD Data (23pm GMT+1, 17pm EST)
quotes = yf.download(config()["ticker"], period="1d")["Adj Close"]

# *Transform*: Needed transforms for Inserting in db
# recoding
quotes.columns = [
    iso_code.replace("EUR","").replace("=X","") for iso_code in quotes.columns
]
# changing index type (datetime -> str) and label name
quotes.index = quotes.index.strftime("%Y-%m-%d")
quotes.index.rename("date", inplace=True)
# melting (tidy format)
quotes_tidy = quotes.melt(            
        var_name="code",
        value_name="price",
        ignore_index=False
).reset_index().sort_values(by=["date","code"])    

with open("secrets.json","r") as f:
    data_json = json.load(f)   

secrets = data_json["sql_authentication"]

try:
    conn = msql.connect(
        host='localhost', 
        database='finance_market_data_db', 
        user=secrets["username"], 
        password=secrets["password"]
    )
    if conn.is_connected():
        cursor = conn.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)        
        #loop through the data frame
        for i,row in quotes_tidy.iterrows():
            #here %S means string values 
            sql = "INSERT INTO fx_prices(date, code, price) VALUES (%s,%s,%s);"
            cursor.execute(sql, tuple(row))
            print("Record inserted")
            # the connection is not auto committed by default, so we must commit to save our changes
            conn.commit()
except Error as e:
    print("Error while connecting to MySQL", e)

#Missing points:
"""
1. ETL (Extract from Y!, Transform pandas df, Load into SQL Server)
2. `crontab -e` for schedule daily batch execution on SQL MariaDB Linux Server 
(raspi4 arm64)
3. Expand YAML or SQL Table to a more extensive Universe of Assets
"""
