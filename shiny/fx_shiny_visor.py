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

from pathlib import Path

from datetime import datetime, timedelta

CONFIG_FILE = "./config.yaml"

# static fun
def config():
        with open(CONFIG_FILE,"r") as configfile:
            cfg=yaml.safe_load(configfile)
        
        countries = list()
        
        for land in cfg["currencies"].keys():
            countries.extend(cfg["currencies"][land])

        return countries

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
            selected=["USD","CHF"],
            multiple=True,
            selectize=True,
            width="65%"

        ),
        ui.output_ui("range_date_picker"),  
        ui.input_switch(
            "lock_dates",
            "Lock Date Window",
            value=True
        ),
        ui.h4("FX-Portfolio Diversification"),
        ui.input_radio_buttons(
            id="blending_type",
            label="Type of Portfolio blending:",
            choices={
                "ew": "Equally Weighted",
                "iv": "Inverse-Volatility Weighted"
            },
            selected="iv",
            inline=True
        ),
        ui.output_ui("target_vol"),                          
        ui.output_ui("target_vol_text"),
        #ui.input_action_button("go", "Submit Changes", class_="btn-success")
        ),
        ui.panel_main(
            ui.page_navbar(                
                ui.nav_menu(
                    "Dynamic Analysis of Returns",
                    ui.nav(
                        "Nondiversified",
                        ui.h3("Chart of Total Return"),
                        ui.markdown(
                            """ 
                            ##### Hypothetical Growth of 10,000€
                            Individual (nondiversified) growth for each currency chosen.
                            """
                        ),
                        ui.output_plot("plot_undiv")
                    ),
                    ui.nav(
                        "Diversified",
                        ui.row(
                            ui.column(8,
                                ui.h3("Chart of Total Return"),
                                ui.output_ui("text_div"),
                                ui.output_plot("plot_div")
                            ),
                            ui.column(4,
                                ui.h3("Distribution"),                            
                                ui.output_table("alloc_div")                            
                            )
                        ),
                        ui.row(
                            ui.column(6,
                                ui.h4("Positions Disclosure"),
                                ui.markdown(
                                    """  
                                    EUR position distinct of zero reflects portion of the initial investment allocated to the risk-free currency wrt to the relevant risk factor.
                                    """
                                ),                           
                                ui.output_plot("pie_alloc_div"),                            
                            )
                        )
                    )   
                ),
                ui.nav(
                    "Volatility Risk",                    
                ),
                ui.nav_spacer(),
                ui.nav_control(
                    ui.a(
                        "FX LETOR",
                        href="https://github.com/falken1983/fx_letor",
                        target='_blank'
                    )                    
                )
            )
        )
    )
)

def server(input, output, session):
    
    type = {
            "ew": "Equally Weighted",
            "iv": "Inverse-Volatility Weighted",
        }

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
    def range_date_picker():        
        
        if input.lock_dates():
            with reactive.isolate():
                start_ = fetch_and_clean().index[0].strftime("%Y-%m-%d")
                end_ = fetch_and_clean().index[-1].strftime("%Y-%m-%d")               
        else:
            start_ = fetch_and_clean().index[0].strftime("%Y-%m-%d")
            end_ = fetch_and_clean().index[-1].strftime("%Y-%m-%d")               
        
        return ui.input_date_range(
            id="date_range",
            label="Pick Dates:",                        
            start=start_,
            end=end_,
            min=start_,
            max=end_,
            separator="to",
            weekstart=1,
            language="gb"
        )       

    # The Slicers Block
    @reactive.Calc
    def raw_px():                
        start_date = input.date_range()[0]
        end_date = input.date_range()[1]
        return fetch_and_clean()[start_date:end_date]

    @reactive.Calc
    def normalized_px():                
        fx_prices = raw_px()        
        return 10000*fx_prices/fx_prices.iloc[0,:] 

    # The Portfolio/Allocations Block (ew is trivial)
    @reactive.Calc
    def ew_port_cumret():
        return 10000*(1+normalized_px().pct_change().fillna(0).mean(axis=1)).cumprod()

    @reactive.Calc
    def iv_factor_weigths():
        vol_targetting = 0.01*input.port_vol()
        vol_targetting/=np.sqrt(252)
        factors = vol_targetting/raw_px().pct_change().std()
        factors[factors>1]=1 #DKK patology (pegged to EUR). It acts as a risk-free currency ~EUR
        return factors

    @reactive.Calc
    def iv_port_cumret():        
        weighted_returns = iv_factor_weigths().values.reshape(-1,1).T*raw_px().pct_change().fillna(0)
        return 10000*(1+weighted_returns.mean(axis=1)).cumprod()
    
    @output
    @render.plot
    #@reactive.event(input.go)
    def plot_undiv():

        _, ax = plt.subplots()        
        
        ax.plot(normalized_px())
        plt.tick_params(rotation=45)
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%b'))
        ax.set_ylabel("Cumulative Wealth (€)")
        ax.legend(normalized_px().columns.tolist(),frameon=False)
        plt.grid(visible=True, axis='y')         
       
    @output
    @render.ui
    #@reactive.event(input.blending_type)
    def target_vol():
        if input.blending_type()=="iv":
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
    #@reactive.event(input.port_vol, ignore_none=False)
    def target_vol_text():
        if input.blending_type()=="iv":
            return ui.markdown(
            f"""            
            Current portfolio volatility set to {input.port_vol():.1f}%
            """
        )
        return None

    @output
    @render.ui
    def text_div():
        curncies = input.symbols()
        
        return ui.markdown(
            f"""
            ##### Hypothetical Growth of 10,000€ 
            {type[input.blending_type()]} Portfolio composed by {', '.join(curncies)}
            """
        )

    @output
    @render.plot
    #@reactive.event(input.go)
    def plot_div():        

        _, ax = plt.subplots()                       

        if input.blending_type()=="ew":
            ax.plot(normalized_px(), alpha=0.15)
            ax.plot(ew_port_cumret(), color="black")        
        else:            
            ax.plot(normalized_px(), alpha=0.075)
            ax.plot(ew_port_cumret(), color="black", linestyle="dashdot", alpha=0.36, label="Equally Weighted")
            ax.plot(iv_port_cumret(), color="black", label="Volatility Targetting")            
            ax.legend(frameon=False)        
        
        plt.tick_params(rotation=45)
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%b'))
        ax.set_ylabel("Cumulative Wealth (€)")
        plt.grid(visible=True, axis='y')

    @output
    @render.table
    #@reactive.event(input.go)
    def alloc_div():
        weights = 10000*iv_factor_weigths().to_frame(name="Allocation")
        weights /= weights.shape[0]
        
        if input.blending_type()=="ew":
            weights = pd.DataFrame(
                10000/weights.shape[0],
                index=weights.index,
                columns=["Allocation"]
            )
            
        return (
            weights    
            .reset_index()            
            .rename(columns={"index": "Currency"})
            .style
            .set_table_attributes(
                'class="dataframe shiny-table table w-auto"'
            )
            .format({"Allocation": "{:.0f}€"})
            .hide(axis="index")                      
        )

    @output
    @render.plot
    #@reactive.event(input.go)
    def pie_alloc_div():
        omega=iv_factor_weigths()
        y_fx = omega.values/len(omega)
        y = np.append(y_fx,1-np.sum(y_fx))
        
        if input.blending_type()=="ew":
            y=np.array([1]*len(omega))/len(omega)

        curncies = omega.index.to_list()
        
        if input.blending_type()=="iv":
            curncies.extend(["EUR"])              

        _, ax = plt.subplots(figsize=(10,7))

        explode_ = [0]*len(curncies)
        
        if input.blending_type()=="iv":
            explode_[-1] = 0.1

        ax.pie(y,
            labels=curncies,
            autopct="%1.1f%%",
            explode=explode_,
            shadow=True,            
        )


app = App(app_ui, server)