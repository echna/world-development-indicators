
'''
run the comand below in cmd before using this notebook
bokeh serve wdi_plots.py
then in your browser go to http://localhost:5006/wdi_plots
'''

import os, platform
import numpy as np
import pandas as pd
import scipy as sp

import sqlite3

import matplotlib.pyplot as plt

from bokeh.plotting import Figure, show, output_file, ColumnDataSource
from bokeh.models import HoverTool, ColumnDataSource, HBox, VBoxForm, Select
from bokeh.models.widgets import Slider
from bokeh.io import curdoc

	
# ******  FUNCTIONS  ******

def Indicator_group(str):
	'''given the start of an IndicatorCode this function returns all IndicatorNames of that subgroup of indicators'''
	return indicator_df[indicator_df.IndicatorCode.str.contains(str)==True].drop_duplicates('IndicatorName')	

def Indicator_Name_f(Indicator_Code):
	'''generates IndicatorName from Code'''
	return indicator_df.IndicatorName[indicator_df.IndicatorCode==Indicator_Code].values.astype(str)[0]

def axis_values(Indicator_Code, year, countries):
	"""get values for the Indicators for selected year and countries"""
	return indicator_df.Value[(indicator_df.IndicatorCode==Indicator_Code) & (indicator_df.Year==year) & (indicator_df.CountryName.isin(countries)) ]

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
	return pd.read_sql_query("SELECT * FROM Indicators WHERE IndicatorName LIKE @x GROUP BY IndicatorName LIMIT 10",
		conn,  params={'x': '%'+str +'%'})

def scatter_plot( Indicator_Code_x = 'SP.DYN.IMRT.IN',Indicator_Code_y = 'SH.XPD.PUBL.ZS',Indicator_Code_z='SP.DYN.CBRT.IN',Year_1 = 2010):
	'''generate scatter plot for choosen year with x and y axis and area of scatter spots as z axis '''
	
	#get countries for the selected indicators
	query_str=str(
	"SELECT CountryName FROM Indicators WHERE IndicatorCode=:x AND Year=:n "
	+"UNION SELECT CountryName FROM Indicators WHERE IndicatorCode=:y AND Year=:n  "
	+"UNION SELECT CountryName FROM Indicators WHERE IndicatorCode=:z AND Year=:n "
	)
	
	countries= tuple(pd.read_sql_query( query_str,conn, params={'x': Indicator_Code_x,'y': Indicator_Code_y,'z': Indicator_Code_z, 'n': Year_1}).astype(str).values[:,0])

	
	# labeling the axis 
	plt.xlabel(str(Indicator_Name_f(Indicator_Code_x)))
	plt.ylabel(str(Indicator_Name_f(Indicator_Code_y)))

	# giving the source of the plot marker area in the title. Maybe change to legend
	plt.title("area=" +str(Indicator_Name_f(Indicator_Code_z)))
	
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

	#initialize data
	#get countries for the selected indicators, convert to string, and tuple and sort alphabetically
	countries= tuple(sorted(pd.unique(pd.concat([
		indicator_df.CountryName[indicator_df.IndicatorCode==Indicator_Code_x],
		indicator_df.CountryName[indicator_df.IndicatorCode==Indicator_Code_y],
		indicator_df.CountryName[indicator_df.IndicatorCode==Indicator_Code_z]]).astype(str).values)))
	
	# defining x and y values
	x = axis_values(Indicator_Code_x, Year_1,countries)
	y = axis_values(Indicator_Code_y, Year_1,countries)
	z = axis_values(Indicator_Code_z, Year_1,countries)
	z_normalisation = max(z)

	#pack source data
	source = ColumnDataSource(data=dict(
	            x=x,
	            y=y,
	            countries=sorted(countries),
	            z=.5*z/z_normalisation
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
	p = Figure(tools=[hover, "pan,box_zoom,reset,resize,save,wheel_zoom"])
	
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
	p.scatter('x','y', radius='z', source=source, alpha=.5)
	
	# generate selection options for the axis. VERY slow if the set of indicators is too large. For example 'SH' only takes forever.
	#print Indicator_group('SH.XPD')
	indicator_options_x = Indicator_group('.').set_index('IndicatorName')['IndicatorCode'].to_dict()  #default value is 'SH.XPD' for now
	indicator_options_y = Indicator_group('.').set_index('IndicatorName')['IndicatorCode'].to_dict()  #default value is 'SP.DYN' for now
	indicator_options_z = Indicator_group('.').set_index('IndicatorName')['IndicatorCode'].to_dict()  #default value is 'SP.DYN' for now
	
	# Set up widgets
	year = Slider(title="Year", value=Year_1, start= 1990 , end=2015, step=1)
	indicator_x_select = Select(value=Indicator_Name_f(Indicator_Code_x), title='Indicator on x-axis', options=sorted(indicator_options_x.keys()))
	indicator_y_select = Select(value=Indicator_Name_f(Indicator_Code_y), title='Indicator on y-axis', options=sorted(indicator_options_y.keys()))
	indicator_z_select = Select(value=Indicator_Name_f(Indicator_Code_z), title='Indicator as spot area', options=sorted(indicator_options_z.keys()))
	
	# Set up callbacks
	def update_title(attrname, old, new):
		p.title = ("Year=" +str(year.value)
			+ " -- Spot area ~" + str(indicator_z_select.value)   )
	
	def update_xaxis(attrname, old, new):
		p.xaxis.axis_label = str(indicator_x_select.value)

	def update_yaxis(attrname, old, new):
		p.yaxis.axis_label = str(indicator_y_select.value)
	
	def update_data(attrname, old, new):
		#get countries for the selected indicators, convert to string, and tuple and sort alphabetically
		countries= tuple(sorted(pd.unique(pd.concat([
		indicator_df.CountryName[indicator_df.IndicatorCode==Indicator_Code_x],
		indicator_df.CountryName[indicator_df.IndicatorCode==Indicator_Code_y],
		indicator_df.CountryName[indicator_df.IndicatorCode==Indicator_Code_z]]).astype(str).values)))

		# regenerate values
		x = axis_values(indicator_options_x[indicator_x_select.value],  year.value,countries)
		y = axis_values(indicator_options_y[indicator_y_select.value],  year.value,countries)
		y = axis_values(indicator_options_z[indicator_z_select.value],  year.value,countries)
		#max() gives errors for empty sets 
		z_normalisation = max(z)

		source.data = dict(
	        x=x,
	        y=y,
	        countries=sorted(countries),
	        z=.5*z/z_normalisation
	    )
	
	#set updates    
	indicator_x_select.on_change('value', update_data)
	indicator_x_select.on_change('value', update_xaxis)
	indicator_y_select.on_change('value', update_data)
	indicator_y_select.on_change('value', update_yaxis)
	indicator_z_select.on_change('value', update_data)
	indicator_z_select.on_change('value', update_title)
	year.on_change('value', update_title)
	year.on_change('value', update_data)


	# Set up layouts and add to document
	inputs = VBoxForm(children=[year,indicator_x_select,indicator_y_select,indicator_z_select])

	curdoc().add_root(HBox(children=[inputs, p]))


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


	
# ******  Main  ******

#get base directory and OS
orig_dir = os.getcwd()

#select correct path depending on OS
if os.name =='posix':
	os.chdir(orig_dir +'/world-development-indicators-data')
elif os.name=='nt':
	os.chdir(orig_dir +'\world-development-indicators-data')

#load data
conn = sqlite3.connect('database.sqlite')

#codes = pd.read_sql_query("SELECT IndicatorCode FROM Indicators ",conn).values[:,0]
#codes_unique = np.unique([str(i[:2]) for i in codes])

#unigue first 2 letters of IndicatorCodes
codes_unique = np.array(['AG', 'BG', 'BM', 'BN', 'BX', 'CM', 'DC', 'DT', 'EA', 'EG', 'EN',
       'EP', 'ER', 'FB', 'FD', 'FI', 'FM', 'FP', 'FR', 'FS', 'GB', 'GC',
       'IC', 'IE', 'IP', 'IQ', 'IS', 'IT', 'LP', 'MS', 'NE', 'NV', 'NY',
       'PA', 'PX', 'SE', 'SG', 'SH', 'SI', 'SL', 'SM', 'SN', 'SP', 'ST',
       'TG', 'TM', 'TT', 'TX', 'VC', 'pe'],
      dtype='|S2')

#reduced set for debugging and testing
indicator_list=('SH.XPD.PUBL.ZS'  ,'SP.DYN.IMRT.IN' ,'SP.DYN.CBRT.IN', 'AG.PRD.CREL.MT', 'BM.GSR.FCTY.CD', 'EN.CO2.TRAN.ZS', 'AG.LND.ARBL.HA', 'DT.DOD.DSTC.ZS', 'EG.ELC.NUCL.ZS', 'EN.CO2.TRAN.ZS')
indicator_df = pd.read_sql_query("SELECT * FROM Indicators WHERE IndicatorCode in" +str(indicator_list) ,  conn)

#indicator_df = pd.read_sql_query("SELECT * FROM Indicators",  conn)

Indicator_Code_x = 'SH.XPD.PUBL.ZS'  #Mortality rate, infant (per 1,000 live births)
Indicator_Code_y = 'SP.DYN.IMRT.IN'	 #Health expenditure, public (% of GDP)
Indicator_Code_z = 'SP.DYN.CBRT.IN'  #Birth rate, crude (per 1,000 people)

Year_1=2010

scatter_plot2(Indicator_Code_x ,Indicator_Code_y ,Indicator_Code_z,Year_1)

os.chdir(orig_dir)
