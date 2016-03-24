
import numpy as np
import pandas as pd
import scipy as sp
import seaborn as sns
import sqlite3
import matplotlib.pyplot as plt

import os
previous_dir = os.getcwd()

os.chdir(previous_dir +'\world-development-indicators-data')

store_Country = pd.HDFStore('Country')
store_indicators = pd.HDFStore('Indicators')

# Indicators = pd.read_csv('Indicators.csv',parse_dates=[0], infer_datetime_format=True)
# store_indicators['Indicators'] = Indicators
# Country = pd.read_csv('Country.csv',parse_dates=[0], infer_datetime_format=True)
# store_Country['Country'] = Country

Country = store_Country['Country']
Indicators = store_indicators['Indicators']

conn = sqlite3.connect('database.sqlite')

# names of tables for orientation
table_names = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table' ",  conn)
			   # name
	# 0       Country
	# 1  CountryNotes
	# 2        Series
	# 3    Indicators
	# 4   SeriesNotes
	# 5     Footnotes

	
# ******  FUNCTIONS  ******
	
	
def Indicator_Name_f(Indicator_Code):
	'''generates Indicator_Name from Code'''
	return pd.read_sql_query("SELECT IndicatorName FROM Indicators WHERE IndicatorCode=:y LIMIT 1",conn, params={'y': Indicator_Code}).values[0,0]

def time_and_values(Country_Name,Indicator_Code):
	'''generates values for Country_Name  and Indicator_Code indexed by the year'''
	data = pd.read_sql_query("SELECT Year,Value FROM Indicators WHERE CountryName=:x AND IndicatorCode=:y ",
	  conn, 
	  params={'x': Country_Name, 'y': Indicator_Code})
	# set index to year
	data.set_index('Year', inplace = True)
	return data

	
# ******  Plotting  ******
	
	
Indicator_Code ='AG.YLD.CREL.KG'
	
plt.title(str(Indicator_Name_f(Indicator_Code)))
plt.plot(time_and_values('Germany',Indicator_Code), 'r')
plt.plot(time_and_values('France',Indicator_Code), 'b')
plt.show()

os.chdir(previous_dir)