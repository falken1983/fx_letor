import streamlit as st
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter

import yfinance as yf
import yaml

from datetime import datetime, timedelta

plt.style.use("fast")

PATH_STREAMLIT_APP = "/app/fx_letor/streamlit/"
CONFIG_FILE = "config.yaml"
FULLPATH_CONFIG_FILE = PATH_STREAMLIT_APP + CONFIG_FILE

try:
    with open(FULLPATH_CONFIG_FILE,"r") as configfile:
        cfg=yaml.safe_load(configfile)
except:
    with open(CONFIG_FILE,"r") as configfile:
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
fx_prices.columns = [x.replace("EUR","").replace("=X","") for x in fx_prices.columns.tolist()]

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

        refreshed= st.form_submit_button("Submit")

    if refreshed:
        st.success("Succesfully Updated",icon="💸")
    else:
        st.warning("Awaiting Submit Button...",icon="⌛")

    st.title ("FX-Portfolio Allocation")
    opciones = st.radio('Choose Currency blending scheme:', ['Equally Weighted', 'Inverse-Volatility Weighted'])
    ew = False

    if opciones == "Equally Weighted":
        ew = True
    else:
        target_vol = st.number_input(
            'Insert target portfolio volatility',
            min_value=1.0,
            max_value=15.0,
            step=0.25,
            value=5.0
            )
        st.write(f'Current portfolio volatility is set to {target_vol}%')
        target_vol /= 100            

# Common DataFrames
norm_fx_px = 10000*fx_prices[start_date:end_date][symbols]/fx_prices[start_date:end_date][symbols].iloc[0,:]
fx_px = fx_prices[start_date:end_date][symbols]

# Main Layout
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
        plt.grid(visible=True, axis='y')
        # st decorations
        st.markdown("#### Hypothetical Growth of 10,000€")
        st.write("Individual (nondiversified) growth for each currency chosen.")
        st.pyplot(fig)        

with tab2:
    st.header("Diversified")    
    col1, col2 = st.columns([3,1])
    
    if refreshed:  
        st.balloons()      
        # Solomonic Blending
        fx_port_cumret = 10000*(1+norm_fx_px.pct_change().mean(axis=1)).cumprod()        
        fig, ax = plt.subplots()        
        if ew:                               
            with col1:                
                # EW Blending
                ax.plot(norm_fx_px, alpha=0.15)
                ax.plot(fx_port_cumret, color="black")
                plt.tick_params(rotation=45)
                ax.xaxis.set_major_formatter(DateFormatter('%Y-%b'))
                ax.set_ylabel("Cumulative Wealth (€)")
                plt.grid(visible=True, axis='y')
                            
                st.markdown("#### Hypothetical Growth of 10,000€")                            
                curncy_components = f'{", ".join(symbols)}'            
                st.markdown(f"{opciones} Portfolio composed by " + curncy_components)
                st.pyplot(fig)        
            with col2:                
                st.markdown(f"#### Total Return")
                st.metric(
                    label="Net Gains",
                    value=f"{fx_port_cumret.iloc[-1]-10000:.2f}€",
                    delta=f"{100*(1e-4*fx_port_cumret.iloc[-1]-1):.1f}%"
                )        
        else:   # Invers-Vol Blending                     
            with col1:                                
                target_vol/=np.sqrt(252)
                factors = target_vol/fx_px.pct_change().std()
                factors[factors>1]=1 #DKK patology (pegged to EUR). It acts as a risk-free currency ~EUR
                weighted_returns = factors.values.reshape(-1,1).T*fx_px.pct_change()
                fx_iv_port_cumret = 10000*(1+weighted_returns.mean(axis=1)).cumprod()

                ax.plot(norm_fx_px, alpha=0.075)
                ax.plot(fx_port_cumret, color="gray", linestyle="dotted", alpha=0.45, label="Equally Weighted")
                ax.plot(fx_iv_port_cumret, color="black", label="Volatility Targetting")
                plt.tick_params(rotation=45)
                ax.xaxis.set_major_formatter(DateFormatter('%Y-%b'))
                ax.set_ylabel("Cumulative Wealth (€)")
                plt.grid(visible=True, axis='y')
                ax.legend(frameon=False)
            
                st.markdown("#### Hypothetical Growth of 10,000€")                            
                curncy_components = f'{", ".join(symbols)}'            
                st.markdown(f"{opciones} Portfolio composed by " + curncy_components)
                st.pyplot(fig)
            with col2:                
                st.markdown(f"#### Total Return")
                st.metric(
                    label="Net Gains",
                    value=f"{fx_iv_port_cumret.iloc[-1]-10000:.2f}€",
                    delta=f"{100*(1e-4*fx_iv_port_cumret.iloc[-1]-1):.1f}%"
                )
                
                st.markdown("#### Distribution")                                
                iv_weights = 10000*factors.to_frame(name="Allocation")
                iv_weights /= iv_weights.shape[0]                                                
                st.dataframe(
                    iv_weights.style.format({"Allocation": "{:.0f}€"}),             
                )