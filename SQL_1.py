
import numpy as np
import pandas as pd
import scipy as sp
import seaborn as sns
import sqlite3
import matplotlib.pyplot as plt

import os
previous_dir = os.getcwd()

os.chdir(previous_dir +'\world-development-indicators-data')

# store_Country = pd.HDFStore('Country')
# store_indicators = pd.HDFStore('Indicators')

# # Indicators = pd.read_csv('Indicators.csv',parse_dates=[0], infer_datetime_format=True)
# # store_indicators['Indicators'] = Indicators
# # Country = pd.read_csv('Country.csv',parse_dates=[0], infer_datetime_format=True)
# # store_Country['Country'] = Country

# Country = store_Country['Country']
# Indicators = store_indicators['Indicators']

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

def Indicator_finder(str):
	'''given a string lists the first 10 indictors that contain this string'''
	return pd.read_sql_query("SELECT * FROM Indicators WHERE IndicatorName LIKE @x GROUP BY IndicatorName LIMIT 10",conn,  params={'x': '%'+str +'%'})
	
	
# ******  Plotting  ******

# Choosing indicators and Year to be plotted
# Looking up indicators is still a pain. Would be good to drop all the indicators that have only few years and countries from the data file. Better make a copy of the sql file before attempting that ;)
Indicator_Code_x ='SP.DYN.IMRT.IN' #	Mortality rate, infant (per 1,000 live births)
Indicator_Code_y ='SH.XPD.PUBL.ZS' #	Health expenditure, public (% of GDP)
Indicator_Code_z ='SH.STA.ACSN.UR' #	Improved sanitation facilities, urban (% of urban population with access)4
Year_1 = 2010 #Would be nice to animate through several years, potentially with the circels drawing a path each over the years

countries = ('Germany', 'France', 'Poland', 'Austria', 'Taiwan', 'China', 
	'Mexico', 'Brazil','Pakistan', 'Japan', 'Spain', 'Greece', 'Turkey','Lybia',
	'Namibia','Angola','Mali', 'Estonia','Israel','Irak', 'Iran', 'Chile','Columbia',
	'Sudan','Uganda','Algeria', 'Australia',  'Egypt', 'Italy', 'Russia', 'Denmark', 'India')
	
# This doesnt work yet. Would be nice to select countries automatically if they have data for the indicators x y and z and required Year(s) available
#str(tuple(Country_Name[0].encode('utf-8')for Country_Name in 
#	pd.read_sql_query("SELECT CountryName FROM Indicators WHERE IndicatorCode=:x AND IndicatorCode=:y AND IndicatorCode=:z AND Year=:n  LIMIT 100 ",conn, params={'x': Indicator_Code_x,'y': Indicator_Code_y,'z': Indicator_Code_z, 'n': Year_1}).values))
#pd.read_sql_query("SELECT IndicatorName, IndicatorCode FROM Indicators GROUP BY IndicatorName HAVING COUNT(DISTINCT Year) = 56 LIMIT 100", conn)


# labeling the axis 
plt.xlabel(str(Indicator_Name_f(Indicator_Code_x)))
plt.ylabel(str(Indicator_Name_f(Indicator_Code_y)))
# giving the source of the plot marker area in the title. Maybe change to legend
plt.title("area=" +str(Indicator_Name_f(Indicator_Code_z)))

#normalisation of the plot marker size
area_normalisation  = sum(pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN " +str(countries),
	conn, params={'x': Indicator_Code_z, 'n': Year_1}).values)/(len(countries))	
# defining x and y values
x = pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries),
	conn, params={'x': Indicator_Code_x, 'n': Year_1}).values
y = pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries),
	conn, params={'x': Indicator_Code_y, 'n': Year_1}).values
# plotmarkersize, it's been normalised, squared and multiplied by 100 to give a visible change in size. This is not necessariliy a good representation
area = 100*(pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries),
	conn, params={'x': Indicator_Code_z, 'n': Year_1}).values/area_normalisation)**2

plt.scatter(x, y, s=area, alpha=0.5)
plt.show()



	
Indicator_Code ='AG.YLD.CREL.KG'


#plots for a bunch of countries for just one indicator
plt.figure()
for Country_Name in [str(Country_Name[0].encode('utf-8'))for Country_Name in pd.read_sql_query("SELECT ShortName  FROM Country LIMIT 10 ",conn).values]:
	plt.plot(time_and_values(Country_Name,Indicator_Code))

plt.show()

plt.title(str(Indicator_Name_f(Indicator_Code)))
plt.plot(time_and_values('Germany',Indicator_Code), 'r')
plt.plot(time_and_values('France',Indicator_Code), 'b')
plt.plot(time_and_values('United Kingdom',Indicator_Code), 'g')
plt.show()

os.chdir(previous_dir)