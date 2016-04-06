
import os, platform
import numpy as np
import pandas as pd
import scipy as sp

import sqlite3

import matplotlib.pyplot as plt

from bokeh.plotting import Figure, show, output_file
from bokeh.models import HoverTool,ColumnDataSource, HBox, VBoxForm
from bokeh.models.widgets import Slider
from bokeh.io import curdoc

#get base directory and OS
orig_dir = os.getcwd()

#select correct path depending on OS
if os.name =='posix':
	os.chdir(orig_dir +'/world-development-indicators-data')
elif os.name=='nt':
	os.chdir(orig_dir +'\world-development-indicators-data')


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
	return pd.read_sql_query("SELECT IndicatorName FROM Indicators WHERE IndicatorCode=:y LIMIT 1",
		conn, params={'y': Indicator_Code}).values[0,0]

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
	return pd.read_sql_query("SELECT * FROM Indicators WHERE IndicatorName LIKE x GROUP BY IndicatorName LIMIT 10",
		conn,  params={'x': '%'+str +'%'})

def scatter_plot( Indicator_Code_x = 'SP.DYN.IMRT.IN',Indicator_Code_y = 'SH.XPD.PUBL.ZS',Indicator_Code_z='SP.DYN.CBRT.IN',Year_1 = 2010):
	'''generate scatter plot for choosen year with x and y axis and area of scatter spots as z axis '''
	
	#######  Needs more automisation in general in particular taking care of missing values before ca 1980
	
	# needs some checks to exclude data, which does not have all three indicators for the specified year
	
	# Choosing indicators and Year to be plotted
	# Looking up indicators is still a pain. Maybe construct a shortlist of indicators which are obviously related to heath issues
	# Indicator_Code_x ='SP.DYN.IMRT.IN' #	Mortality rate, infant (per 1,000 live births)
	# Indicator_Code_y ='SH.XPD.PUBL.ZS' #	Health expenditure, public (% of GDP)
	# Indicator_Code_z ='SP.DYN.CBRT.IN' #	Birth rate, crude (per 1,000 people)
	# Year_1 = 2010 #Would be nice to animate through several years, potentially with the circels drawing a path each over the years

	countries = ('Germany', 'France', 'Poland', 'Austria', 'Taiwan', 'China', 'Mexico', 'Brazil','Pakistan', 'Japan', 'Spain', 'Greece', 'Turkey','Lybia','Namibia','Angola','Mali', 'Estonia','Israel','Irak', 'Iran', 'Chile','Columbia','Sudan','Uganda','Algeria', 'Australia',  'Egypt', 'Italy', 'Russia', 'Denmark', 'India')
		
	# This doesnt work yet. Would be nice to select countries automatically if they have data for the indicators x y and z and required Year(s) available
	#str(tuple(Country_Name[0].encode('utf-8')for Country_Name in 
	#	pd.read_sql_query("SELECT CountryName FROM Indicators WHERE IndicatorCode=:x AND IndicatorCode=:y AND 
		# IndicatorCode=:z AND Year=:n  LIMIT 100 ",conn, params={'x': Indicator_Code_x,'y': Indicator_Code_y,'z': Indicator_Code_z, 'n': Year_1}).values))
	#pd.read_sql_query("SELECT IndicatorName, IndicatorCode FROM Indicators GROUP BY IndicatorName HAVING COUNT(DISTINCT Year) = 56 LIMIT 100", conn)


	# labeling the axis 
	plt.xlabel(str(Indicator_Name_f(Indicator_Code_x)))
	plt.ylabel(str(Indicator_Name_f(Indicator_Code_y)))
	# giving the source of the plot marker area in the title. Maybe change to legend
	plt.title("area=" +str(Indicator_Name_f(Indicator_Code_z)))
	
	# add legend for year
	# hover labels for the countries would be nice
	
	#normalisation of the plot marker size
	area_normalisation  = max(pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN " +str(countries),
		conn, params={'x': Indicator_Code_z, 'n': Year_1}).values)#/(len(countries))	
	# defining x and y values
	x = pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries),
		conn, params={'x': Indicator_Code_x, 'n': Year_1}).values
	y = pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries),
		conn, params={'x': Indicator_Code_y, 'n': Year_1}).values
	# plotmarkersize, it's been normalised, squared and multiplied by 200 to give a visible change in size. This is not necessariliy a good representation
	area = 200*(pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries),
		conn, params={'x': Indicator_Code_z, 'n': Year_1}).values/area_normalisation)**1.5

	plt.scatter(x, y, s=area, alpha=.7, c = 'red')
	return plt.show()


def scatter_plot2(Indicator_Code_x ,Indicator_Code_y ,Indicator_Code_z, Year_1 = 2010,):
	'''generate scatter plot with bokeh for choosen year with x and y axis and area of scatter spots as z axis '''

	query_str=str(
	"SELECT CountryName FROM Indicators WHERE IndicatorCode=:x AND Year=:n "
	+"UNION SELECT CountryName FROM Indicators WHERE IndicatorCode=:y AND Year=:n  "
	+"UNION SELECT CountryName FROM Indicators WHERE IndicatorCode=:z AND Year=:n "
	)

	#get countries for the selected indicators
	countries= tuple(pd.read_sql_query( query_str,conn, params={'x': Indicator_Code_x,'y': Indicator_Code_y,'z': Indicator_Code_z, 'n': Year_1}).astype(str).values[:,0])

	# defining x and y values
	x = pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries) + "ORDER BY CountryName",
		conn, params={'x': Indicator_Code_x, 'n': Year_1}).values
	y = pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries) + "ORDER BY CountryName",
		conn, params={'x': Indicator_Code_y, 'n': Year_1}).values
	z = pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries) + "ORDER BY CountryName",
		conn, params={'x': Indicator_Code_z, 'n': Year_1}).values
	z_normalisation = max(z)[0]


	#pack source data
	source = ColumnDataSource(data=dict(
	            x=x[:,0],
	            y=y[:,0],
	            countries=sorted(countries),
	            z=z[:,0]
	        )
	    )

	
	#create hover tooltips
	hover = HoverTool(
	        tooltips=[
	            ("Country", "@countries"),
	            (str(Indicator_Name_f(Indicator_Code_z)), "@z"),
	            ("(x,y)", "(@x, @y)"),
	            ]
	    )

	
	#create figure
	p = Figure(plot_height=600, plot_width=600,tools=[hover, "crosshair,pan,reset,resize,save,wheel_zoom"])
	
	# set title
	p.title = (
		"Year=" +str(Year_1) # a linebreak would be good here, to fit all in the title
		+ " -- Spot area ~" + str(Indicator_Name_f(Indicator_Code_z))   )
	p.title_text_font_size = '12pt'
	p.title_text_align = 'left' # to ensure the year is displayed even for long names of the z-indicator
	
	#set labels
	p.xaxis.axis_label = str(Indicator_Name_f(Indicator_Code_x))
	p.yaxis.axis_label = str(Indicator_Name_f(Indicator_Code_y))
	
	#plot
	p.scatter('x','y', radius=.5*z[:,0]/z_normalisation, source=source, alpha=.5)
	
	# Set up widgets
	year = Slider(title="Year", value=2010, start=2000, end=2015, step=1)

	# Set up callbacks
	def update_data(attrname, old, new):
		# Get the current slider values
		Year_temp  = year.value

		# Generate values
		countries= tuple(pd.read_sql_query( query_str,conn, params={'x': Indicator_Code_x,'y': Indicator_Code_y,'z': Indicator_Code_z, 'n': Year_temp}).astype(str).values[:,0])
		x = pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries) + "ORDER BY CountryName",
			conn, params={'x': Indicator_Code_x, 'n': Year_temp}).values
		y = pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries) + "ORDER BY CountryName",
			conn, params={'x': Indicator_Code_y, 'n': Year_temp}).values
		z = pd.read_sql_query("SELECT Value FROM Indicators WHERE  IndicatorCode=:x AND Year=:n AND CountryName IN" +str(countries) + "ORDER BY CountryName",
			conn, params={'x': Indicator_Code_z, 'n': Year_temp}).values
		z_normalisation = max(z)[0]

		source.data = dict(
			x=x[:,0],
			y=y[:,0],
			countries=sorted(countries),
			z=z[:,0]
	        )

	year.on_change('value', update_data)


	# Set up layouts and add to document
	inputs = VBoxForm(children=[year])

	##not sure what this is meant to do
	#curdoc().add_root(HBox(children=[inputs, p], width=800))

	plot  = HBox(children=[inputs, p], width=1000)
	
	
	output_file("wdi_scatter.html", title="wdi_plot.py")
	show(plot)


def timeseries_plot(countries_tuple= None, Indicator_Code ='SP.DYN.IMRT.IN'):
	plt.figure()
	plt.title(str(Indicator_Name_f(Indicator_Code)))
	if countries_tuple==None:
		for Country_Name in [str(Country_Name[0].encode('utf-8'))for Country_Name in pd.read_sql_query("SELECT ShortName  FROM Country LIMIT 20 ",conn).values]:
			plt.plot(time_and_values(Country_Name,Indicator_Code))
	else:
		for Country_Name in countries_tuple:
			plt.plot(time_and_values(Country_Name,Indicator_Code))
	#plots for a bunch of countries for just one indicator
	return plt.show()


	
# ******  Plotting  ******

#timeseries_plot()

Indicator_Code_x = 'SH.XPD.PUBL.ZS'
Indicator_Code_y = 'SP.DYN.IMRT.IN'
Indicator_Code_z = 'SP.DYN.CBRT.IN'

Year_1=2010

scatter_plot2(Indicator_Code_x ,Indicator_Code_y ,Indicator_Code_z,Year_1)
	

# plt.title(str(Indicator_Name_f(Indicator_Code)))
# plt.plot(time_and_values('Germany',Indicator_Code), 'r')
# plt.plot(time_and_values('France',Indicator_Code), 'b')
# plt.plot(time_and_values('United Kingdom',Indicator_Code), 'g')
# plt.show()

os.chdir(orig_dir)
