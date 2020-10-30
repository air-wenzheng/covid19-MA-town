# -*- coding: utf-8 -*-
"""
Created on Mon May 6 2020

@author: Wenzheng
"""
import pandas as pd
import numpy as np

from bokeh.models import HoverTool, ColumnDataSource
from bokeh.palettes import Viridis6,Viridis3,inferno
from bokeh.plotting import figure, show, output_notebook
from bokeh.models.annotations import Title
import geopandas as gpd
import datetime as dt
import os.path, time

import json
from bokeh.io import show
from bokeh.models import (CDSView, ColorBar, ColumnDataSource,
                          CustomJS, CustomJSFilter, 
                          GeoJSONDataSource, HoverTool,
                          LinearColorMapper, Slider)
from bokeh.layouts import column, row, widgetbox
from bokeh.plotting import figure
import colorcet as cc
import panel as pn
import panel.widgets as pnw

from bokeh.models import LinearColorMapper, LogColorMapper,ColorBar,LogTicker,Ticker
from bokeh.palettes import brewer, viridis

#import os
#os.environ['GDAL_DATA']='C:\ProgramData\Anaconda3\Library\share\gdal'

pn.extension()

shpfile = "MassTown_simple.shp"
# town covid-19 cases (cleaned comprehensive table)
town_csv_file = "covid-19-city-town_recent.csv"

# load data
town_csv_data = pd.read_csv(town_csv_file)
#town_csv_data['POPESTIMATE2018'] = town_csv_data['POPESTIMATE2018'].astype(int)
#town_csv_data['Population_0429'] = town_csv_data['Population_0429'].astype(int)

sf = gpd.read_file(shpfile)

# Merge shapefile with Town COVID-19 data
sf['TOWN'] = sf['TOWN'].str.title()
#town_csv_data['City/Town'] = town_csv_data['City/Town'].str.upper()
covid19_town_ma = sf.merge(town_csv_data, how='left', left_on=['TOWN'], right_on=['City/Town'])

# keep upper boundary of data the same
Count_top = max(covid19_town_ma.filter(regex='Count_').max())
Rate_top = max(covid19_town_ma.filter(regex='Rate_').max())

# Input GeoJSON source that contains features for plotting
geosource = GeoJSONDataSource(geojson = covid19_town_ma.to_json())

tickers = ['Count','Rate']
ticker = pn.widgets.Select(name='Method (Count/Rate)', options=tickers,value=tickers[1],width=200)

temp_variable = list(covid19_town_ma.filter(regex='Count_'))
N_var = len(temp_variable)
tickers1 = [ temp_variable[i].split('_')[1] for i in range(N_var)]

ticker1 = pn.widgets.Select(name='Date of Report (Month-Day)', options=tickers1,value=tickers1[-1],width=200)
tickers2= ['Off','0617','0624','0701','0708','0715','0722','0729','0805','0812','0819','0826','0902','0909','0916','0923','0930','1007','1014','1022','1029']
ticker2 = pn.widgets.Select(name='Weekly Rate Acceleration (Month-Day)', options=tickers2,value=tickers2[0],width=200)

@pn.depends(ticker.param.value,ticker1.param.value,ticker2.param.value)
def bokeh_plot_map(select_item0,select_item1,select_item2):
    select_item = select_item0 +'_' + select_item1
    if select_item2 != 'Off':
        select_item = 'Rate_Acc_' + select_item2
    print('select_item = ',select_item)
    """Plot bokeh map from GeoJSONDataSource """
    # Define color palettes
    #palette = brewer['BuGn'][8]
    #palette = palette[::-1] # reverse order of colors so higher values have darker colors
#    palette = brewer['OrRd'][8]
#    palette = brewer["Spectral"][8]
    palette = cc.coolwarm

#    palette = palette[::-1]
    # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    #color_mapper = LinearColorMapper(palette = palette, low = 0, high = 40000000)
    if select_item0 == 'Count':
        color_mapper = LogColorMapper(palette = palette, low = 1, high = Count_top)
    elif select_item0 == 'Rate':
        color_mapper = LogColorMapper(palette = palette, low = 1, high = Rate_top)

    if select_item2 != "Off":
        palette = cc.coolwarm
        #palette = palette[::-1]
        color_mapper = LinearColorMapper(palette=palette, low=-200, high=200)

    # Define custom tick labels for color bar.
    #tick_labels = {'0': '0', '5': '5','10':'10', '20':'20',
    #     '50':'50','100':'100', '500':'500','1000':'1000+'}
        
    # Create color bar.
    color_bar = ColorBar(color_mapper = color_mapper,
                         ticker=LogTicker(),
                         label_standoff = 8,
                         width = 500, height = 20,
                         border_line_color = None,
                         location = (0,0), 
                         orientation = 'horizontal')

    if select_item2 != 'Off':
        color_bar = ColorBar(color_mapper=color_mapper,
#                             label_standoff=8,
                             width=500, height=20,
                             border_line_color=None,
                             location=(0, 0),
                             orientation='horizontal')

    title ='Comfirmed COVID-19 Cases ' + select_item0 + ' as on ' +  select_item1 + ', 2020 in Each City/Town of Massachusetts'
    if select_item2 != 'Off':
     title = 'Rate Acceleration in confirmed COVID-19 Cases  as on ' + select_item2 + ', 2020 in City/Town of Massachusetts'
    p = figure(title = title,
               plot_height = 700, plot_width =950, 
               toolbar_location = 'above',
               tools = '')
    p.toolbar.logo = None
    p.background_fill_color = "gray"
    p.background_fill_alpha = 0.8
    p.xaxis.visible = False
    p.yaxis.visible = False
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    # Add patch renderer to figure.
    states = p.patches('xs','ys', source = geosource,
                       fill_color = {'field' :select_item,
                                     'transform' : color_mapper},
                       line_color = 'gray', 
                       line_width = 0.25, 
                       fill_alpha = 1)
    # Create hover tool
    p.add_tools(HoverTool(renderers = [states],
                          toggleable= False,  
                          tooltips = [('City/Town','@TOWN'),
                                    (select_item,'@{'+select_item+'}{0,0}')]))
    if select_item2 != 'Off':
        p.add_tools(HoverTool(renderers=[states],
                              toggleable=False,
                              tooltips=[('City/Town', '@TOWN'),
                                        (select_item, '@{' + select_item + '}')]))
    # Specify layout
    p.add_layout(color_bar, 'below')
    return p


text = """
#  Comfirmed COVID-19 Cases in City/Town of Massachusetts

This dashboard shows COVID-19 confirmed cases in each City/Town of Massachusetts. 
Data sources come from the weekly report on ** Confirmed COVID-19 Cases in MA by City/Town (2020)  ** published by MASS. D.P.H. starting from April 14, 2020.

_move mouse over (or finger taps on) a city/town to see the number_
"""

#footnote = '(Last updated on 4:30pm April 14, 2020)'
os.environ['TZ'] = 'US/Eastern'
modTimesinceEpoc = os.path.getmtime(town_csv_file)
modificationTime = dt.datetime.fromtimestamp(modTimesinceEpoc).strftime('%Y-%m-%d %H:%M:%S')

footnote  = """
_Rate is defined as counts per 100,000 people in city/town. For example, if a town has 100 people in population, and has one case, the rate is 1000. 
If a town has 100,0000 people, and one case, the rate is 1. If count < 5, according to the data source, the rate value is defined as zero due to lack of data. 
Basemap resolute drops for better performance._

"""

footnote1 = "_Last updated at: %s (EDT time) by Wenzheng Yang (wenzhengy 'at' gmail.com)_ " % modificationTime


dashboard =pn.Column(pn.Column(text,background="WhiteSmoke",sizing_mode="stretch_width"),pn.Row(ticker,ticker1,ticker2), bokeh_plot_map,pn.Column(footnote,footnote1,background="WhiteSmoke",sizing_mode="stretch_width"),sizing_mode="stretch_height")
dashboard.servable('COVID-19-in-Town-of-MA')
