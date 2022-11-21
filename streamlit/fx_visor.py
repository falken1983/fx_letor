import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter

import yfinance as yf
import yaml
from datetime import datetime, timedelta

plt.style.use("fast")
PATH_STREAMLIT = "/app/fx_letor/streamlit/"

# Load configfile with currencies supported (for mem control)
with open(PATH_STREAMLIT + "config.yaml","r") as configfile:
    cfg=yaml.safe_load(configfile)

# fx_visor alpha supports G11 currencies
with st.sidebar:
    #st.title("Control Panel")
    symbols = st.multiselect(
        label="Please Choose Currency:",
        options=cfg["currencies"]["G11"],
        default="USD"
    )

tickers = ["EUR"+currency+"=X" for currency in cfg["currencies"]["G11"]]

#st.cache??? (caching prices wrt base currency €)
@st.cache
def fetch_and_clean(tickers):
    return 1/yf.download(tickers)["Close"].dropna(how="any")

#adhoc renaming for plotting
fx_prices = fetch_and_clean(tickers)
ytickers = fx_prices.columns.tolist()
currency_names = list()
for sym in ytickers:        
    currency_names.append(sym.replace("EUR","").replace("=X",""))
fx_prices.columns= currency_names

# max time-window
ts_min, ts_max = fx_prices.index[0], fx_prices.index[-1]

# control panel
with st.sidebar:
    
    with st.form("refresh"):
        start_date = st.date_input( # start date 
        "Choose Start Date:",
        min_value = datetime.strptime(ts_min.strftime('%Y-%m-%d'), '%Y-%m-%d'),
        max_value = datetime.strptime(ts_max.strftime('%Y-%m-%d'), '%Y-%m-%d'),        
        value = datetime.strptime(ts_min.strftime('%Y-%m-%d'), '%Y-%m-%d')
        )

        end_date = st.date_input( # end date
            "Choose End Date:",
            min_value = start_date,
            max_value = datetime.strptime(ts_max.strftime('%Y-%m-%d'), '%Y-%m-%d'),        
            value = datetime.strptime(ts_max.strftime('%Y-%m-%d'), '%Y-%m-%d')
        )

        refreshed= st.form_submit_button("Refresh!")

    st.title ("FX-Portfolio Allocation")
    opciones = st.radio('Choose Currency blending scheme:', ['Equally Weighted', 'Inverse-Volatility Weighted'])
    ew = False
    if opciones == "Equally Weighted":
        ew = True

norm_fx_px = 10000*fx_prices[start_date:end_date][symbols]/fx_prices[start_date:end_date][symbols].iloc[0,:]

st.header("FX Visor")

tab1, tab2 = st.tabs(["Nondiversified", "Diversified"])

with tab1:
    st.header("Nondiversified")    

    if refreshed:        
        fig, ax = plt.subplots()
        ax.plot(norm_fx_px)
        #ax.plot(sdata_yearacum[cities])
        plt.tick_params(rotation=45)
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%b'))
        ax.set_ylabel("Cumulative Wealth (€)")
        ax.legend(symbols, frameon=False)
        # st decorations
        st.markdown("#### Hypothetical Growth of 10,000€")
        st.write("Individual (nondiversified) growth for each currency chosen.")
        st.pyplot(fig)

with tab2:
    st.header("Diversified")
    #st.write("`bla bla bla`")       
    
    if refreshed:
        if ew:
            fx_port_cumret = 10000*(1+norm_fx_px.pct_change().mean(axis=1)).cumprod()

            fig, ax = plt.subplots()
            ax.plot(norm_fx_px, alpha=0.15)
            ax.plot(fx_port_cumret, color="black")
            plt.tick_params(rotation=45)
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%b'))
            ax.set_ylabel("Cumulative Wealth (€)")
            #ax.legend(symbols, frameon=False)
            
            st.markdown("#### Hypothetical Growth of 10,000€:")            
            #st.markdown(f"{opciones} Portfolio is composed by {symbols[0]}")

            curncy_components = f'{", ".join(symbols)}'            
            st.markdown(f"{opciones} Portfolio composed by " + curncy_components)
            st.pyplot(fig)
        else:
            st.markdown(
                '''
                `fx_visor` is a part of [`fx_letor`](https://github.com/falken1983/fx_letor) is an `alpha` version under heavy development.                
                '''
            )            
            st.markdown(f"**{opciones}** is not supported.")
            #st.write("Please Stay Tuned!")
