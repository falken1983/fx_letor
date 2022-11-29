from shiny import *
from shiny.types import FileInfo
import os
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
import time
import yfinance as yf
import yaml

from datetime import datetime, timedelta

CONFIG_FILE = "./config.yaml"

def config():
        with open(CONFIG_FILE,"r") as configfile:
            cfg=yaml.safe_load(configfile)
        
        countries = list()
        
        for land in cfg["currencies"].keys():
            countries.extend(cfg["currencies"][land])

        return countries

#return ["EUR"+currency+"=X" for currency in countries]

app_ui = ui.page_fluid(
    # Title
    ui.panel_title("📈FX ShinyVisor"),

    # Layout SiderBar
    ui.layout_sidebar(
        ui.panel_sidebar(            
            #ui.input_action_button("connect", "Connect to Y! Finance"),
            ui.input_select(
            "symbols",
            "Pick Currencies",
            choices=config(),
            multiple=True,
            selectize=True
        ),
        ui.output_ui("range_date_picker"),  
        ui.h4("FX-Portfolio Diversification"),
        ui.input_radio_buttons(
            id="blending_type",
            label="Type of Portfolio blending:",
            choices={
                "ew": "Equally Weighted",
                "iv": "Inverse-Volatility Weighted"
            }
        ),
        ui.output_ui("target_vol"),                          
        ui.output_ui("target_vol_text"),
        ui.input_action_button("go", "Submit Changes", class_="btn-success")
        ),
        ui.panel_main(
            ui.navset_pill(
                ui.nav(
                    "Nondiversified",
                    ui.h2("Nondiversified"),
                    ui.markdown(
                        """ 
                        #### Hypothetical Growth of 10,000€
                        Individual (nondiversified) growth for each currency chosen.
                        """
                    ),
                    ui.output_plot("plot_undiv")
                ),
                ui.nav(
                    "Diversified",
                    ui.h2("Diversified"),
                    ui.output_ui("text_div"),
                    ui.output_plot("plot_div")
                )            
            )
        )
    )
)

def server(input, output, session):
    
    @reactive.Calc
    def fetch_and_clean():                
        tickers = ["EUR"+currency+"=X" for currency in input.symbols()]        
        df = 1/yf.download(tickers)["Close"].dropna(how="any")
        if len(input.symbols())==1:
            df = df.to_frame(name=input.symbols()[0])
        else:
            df.columns = [x.replace("EUR","").replace("=X","") for x in df.columns.tolist()]
        return df
    
    @output
    @render.ui
    @reactive.event(input.symbols)
    def range_date_picker():        
        
        start_ = fetch_and_clean().index[0].strftime("%Y-%m-%d")
        end_ = fetch_and_clean().index[-1].strftime("%Y-%m-%d")
        
        return ui.input_date_range(
            id="date_range",
            label="Pick Dates:",            
            start=start_,
            end=end_,
            min=start_,
            max=end_,
            separator=" to ",
            weekstart=1,
            language="gb"
        )       
        
    @output
    @render.plot
    @reactive.event(input.go)
    def plot_undiv():

        start_date = input.date_range()[0]
        end_date = input.date_range()[1]

        fx_prices = fetch_and_clean()[start_date:end_date]        
        norm_fx_px = 10000*fx_prices/fx_prices.iloc[0,:]        

        _, ax = plt.subplots()        
        
        ax.plot(norm_fx_px)
        plt.tick_params(rotation=45)
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%b'))
        ax.set_ylabel("Cumulative Wealth (€)")
        ax.legend(norm_fx_px.columns.tolist(),frameon=False)
        plt.grid(visible=True, axis='y')         
   
    @output
    @render.ui
    def text_div():
        curncies = input.symbols()
        type = {
            "ew": "Equally Weighted",
            "iv": "Inverse-Volatility Weighted",
        }
        return ui.markdown(
            f"""
            #### Hypothetical Growth of 10,000€ 
            {type[input.blending_type()]} Portfolio composed by {', '.join(curncies)}
            """
        )

    @output
    @render.ui
    @reactive.event(input.blending_type)
    def target_vol():
        if input.blending_type()!="ew":
            tgt_gui = ui.input_numeric(
                id="port_vol",
                label="Tune Volatility Target",
                min=3.0,
                max=15.0,
                step=0.2,
                value=5.0
            )                  
            return tgt_gui
        return

    @output
    @render.ui    
    @reactive.event(input.port_vol, ignore_none=True)
    def target_vol_text():
        if input.blending_type()!="ew":
            return ui.markdown(
            f"""            
            Current portfolio volatility set to {input.port_vol():.1f}%
            """
        )
        else:
            return None

    @output
    @render.ui
    def refresh():
        pass

    @output
    @render.plot
    @reactive.event(input.go)
    def plot_div():

        start_date = input.date_range()[0]
        end_date = input.date_range()[1]

        fx_prices = fetch_and_clean()[start_date:end_date]        
        norm_fx_px = 10000*fx_prices/fx_prices.iloc[0,:]        
        fx_port_cumret = 10000*(1+norm_fx_px.pct_change().mean(axis=1)).cumprod()

        _, ax = plt.subplots()                       

        if input.blending_type()=="ew":
            ax.plot(norm_fx_px, alpha=0.15)
            ax.plot(fx_port_cumret, color="black")
            plt.tick_params(rotation=45)
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%b'))
            ax.set_ylabel("Cumulative Wealth (€)")
            plt.grid(visible=True, axis='y')            
        else:
            vol_targetting = 0.01*input.port_vol()
            vol_targetting/=np.sqrt(252)
            factors = vol_targetting/fx_prices.pct_change().std()
            factors[factors>1]=1 #DKK patology (pegged to EUR). It acts as a risk-free currency ~EUR
            weighted_returns = factors.values.reshape(-1,1).T*fx_prices.pct_change()
            fx_iv_port_cumret = 10000*(1+weighted_returns.mean(axis=1)).cumprod()

            ax.plot(norm_fx_px, alpha=0.075)
            ax.plot(fx_port_cumret, color="gray", linestyle="dotted", alpha=0.45, label="Equally Weighted")
            ax.plot(fx_iv_port_cumret, color="black", label="Volatility Targetting")
            plt.tick_params(rotation=45)
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%b'))
            ax.set_ylabel("Cumulative Wealth (€)")
            plt.grid(visible=True, axis='y')
            ax.legend(frameon=False)

app = App(app_ui, server)