
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
	return indicator_df.loc[str].drop_duplicates('IndicatorName')	
	
def Ind_Name_f(Indicator_Code):
	'''generates IndicatorName from Code'''
	return indicator_name_df.reset_index().set_index('IndicatorCode').loc[Indicator_Code].values.astype(str)[0]
	
def Ind_Code_f(Indicator_Name):
	'''returns IndicatorCode from Name'''
	return indicator_name_df.loc[Indicator_Name].values.astype(str)[0]
	
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


# Set up callbacks
def update_group(attrname, old, new):
	"""update dataframe for selected inidcator group"""	
	indicator_df=indicator_all[indicator_all['IndicatorCode'].str.startswith(indicator_group_select.value)]
	print indicator_group_select.value +" loaded"

	indicator_options_x = tuple(indicator_df.drop_duplicates('IndicatorName').IndicatorName.astype(str).values)  

	indicator_x_select.options=sorted(indicator_options_x)
	indicator_y_select.options=sorted(indicator_options_x)
	indicator_z_select.options=sorted(indicator_options_x)

	print indicator_x_select.options[0].values
	indicator_x_select.value=str(indicator_x_select.options[0].values)
	indicator_y_select.value=str(indicator_x_select.options[1])
	indicator_z_select.value=str(indicator_x_select.options[2])

	update_data.indicator_df=indicator_df
	


def update_data(attrname, old, new):
	"""update data for plot"""	
	
	#reshape df
	temp_df=pd.concat(
		[indicator_df.loc[Ind_Code_f(indicator_x_select.value),year.value].set_index('CountryName').rename(columns={"Value": "x"}),
		indicator_df.loc[Ind_Code_f(indicator_y_select.value),year.value].set_index('CountryName').rename(columns={"Value": "y"}),
		indicator_df.loc[Ind_Code_f(indicator_z_select.value),year.value].set_index('CountryName').rename(columns={"Value": "z"})], axis = 1).dropna()
	#reshape df for traces
	temp_df_2 = pd.concat([
		indicator_df.loc[Ind_Code_f(indicator_x_select.value),].set_index('CountryName', append = True).rename(columns={"Value": "x"}),
		indicator_df.loc[Ind_Code_f(indicator_y_select.value),].set_index('CountryName', append = True).rename(columns={"Value": "y"})], axis = 1).dropna()
	temp_df_2.reset_index(inplace = True)
	temp_df_2.drop(['IndicatorName'], axis = 1, inplace = True)
	temp_df_2.set_index('CountryName',inplace = True)
	
	#get countries 
	countries=temp_df.index.astype(str).values
	x=temp_df['x'].values; y=temp_df['y'].values; z=temp_df['z'].values

	x_trace = temp_df_2.loc[trace_country_select.value]['x'].values
	y_trace = temp_df_2.loc[trace_country_select.value]['y'].values
	
	z_normalisation = max(z)

	# updating the labels
	p.title = ("Year=" +str(year.value)+ " -- Spot area ~" + str(indicator_z_select.value)   )
	p.xaxis.axis_label = str(indicator_x_select.value)
	p.yaxis.axis_label = str(indicator_y_select.value)
	
	source.data = dict(
        x=x,
        y=y,
		x_trace = x_trace,
		y_trace = y_trace,
        countries=countries,
        z=area.value*z/z_normalisation
    )
	
# ******  Main  ******

#select correct path depending on OS
if os.name =='posix':
	db_dir='./world-development-indicators-data/'
elif os.name=='nt':
	db_dir='.\world-development-indicators-data'+ "\\"

#load data if db exists
if os.path.exists(db_dir+'database.sqlite'):
	conn = sqlite3.connect(db_dir+'database.sqlite')
else:
	print("Databade (SQLite) for world indicators not found")
	sys.exit(0)

#unigue first 2 letters of IndicatorCodes
codes_unique = np.array(['AG', 'BG', 'BM', 'BN', 'BX', 'CM', 'DC', 'DT', 'EA', 'EG', 'EN',
       'EP', 'ER', 'FB', 'FD', 'FI', 'FM', 'FP', 'FR', 'FS', 'GB', 'GC',
       'IC', 'IE', 'IP', 'IQ', 'IS', 'IT', 'LP', 'MS', 'NE', 'NV', 'NY',
       'PA', 'PX', 'SE', 'SG', 'SH', 'SI', 'SL', 'SM', 'SN', 'SP', 'ST',
       'TG', 'TM', 'TT', 'TX', 'VC', 'pe'],
      dtype='|S2')

codes_unique_df=pd.DataFrame(codes_unique, columns=[ 'Group'])

#load all data
default_indicator_group='SP'
#indicator_all = pd.read_sql_query("SELECT * FROM Indicators",  conn)
#debugging set
indicator_all = pd.read_sql_query("SELECT * FROM Indicators WHERE IndicatorCode LIKE @x ", conn,  params={'x': '%'+ default_indicator_group+'%'})
indicator_df  = indicator_all[indicator_all['IndicatorCode'].str.startswith(default_indicator_group)]

print("data loaded")


#setting start values
Indicator_Code_x = 'SP.DYN.CBRT.IN'
Indicator_Code_y = 'SP.DYN.IMRT.IN'	 
Indicator_Code_z = 'SP.URB.TOTL.IN.ZS' 
Year_init=2010
trace_country  = 'Swaziland'

#get IndidcatorCode and IndicatorName list
indicator_name_df=indicator_df[['IndicatorCode', 'IndicatorName']].set_index('IndicatorName').drop_duplicates('IndicatorCode')

#prepare indicator df
indicator_df.set_index(['IndicatorCode','Year'], inplace = True, drop = True)
indicator_df.drop(['CountryCode'], axis=1, inplace=True)
indicator_df.dropna(inplace=True)



#create figure
hover = HoverTool( tooltips=[("Country", "@countries"), ('Area', "@z"), ("(x,y)", "(@x, @y)")] )
source = ColumnDataSource(data=dict(x=[],y=[],x_trace = [],y_trace = [], countries=[],z=[]))
p = Figure(tools=[hover, "pan,box_zoom,reset,resize,save,wheel_zoom"])
p.scatter('x','y', radius='z', source=source, alpha=.5)
p.line('x_trace','y_trace', source = source, line_width=3,line_alpha=0.6,line_color = 'red')

p.title = (
	"Year=" +str(Year_init) # a linebreak would be good here, to fit all in the title
	+ " -- Spot area ~" + indicator_df.loc[Indicator_Code_z].IndicatorName.astype(str).values[0]   )
p.title_text_font_size = '16pt'
p.title_text_align = 'left' # to ensure the year is displayed even for long names of the z-indicator

#set labels
p.xaxis.axis_label = indicator_df.loc[Indicator_Code_x].IndicatorName.astype(str).values[0]
p.yaxis.axis_label = indicator_df.loc[Indicator_Code_y].IndicatorName.astype(str).values[0]


# generate selection options for the axis. VERY slow if the set of indicators is too large. For example 'SH' only takes forever.
indicator_options_x = tuple(indicator_df.drop_duplicates('IndicatorName').IndicatorName.astype(str).values)  
indicator_options_y = tuple(indicator_df.drop_duplicates('IndicatorName').IndicatorName.astype(str).values)  
indicator_options_z = tuple(indicator_df.drop_duplicates('IndicatorName').IndicatorName.astype(str).values) 
country_options = tuple(indicator_df.drop_duplicates('CountryName').CountryName.values.astype(str))
indicator_group_options = codes_unique_df['Group'].values.astype(str)


# Set up widgets
year = Slider(title="Year", value=Year_init, start= 1960 , end=2015, step=1)
area = Slider(title="Spot Area", value=0.5, start= 0.05 , end=2.0, step=0.05)
indicator_x_select = Select(value=Ind_Name_f(Indicator_Code_x), title='Indicator on x-axis', options=sorted(indicator_options_x))
indicator_y_select = Select(value=Ind_Name_f(Indicator_Code_y), title='Indicator on y-axis', options=sorted(indicator_options_y))
indicator_z_select = Select(value=Ind_Name_f(Indicator_Code_z), title='Indicator as spot area', options=sorted(indicator_options_z))
trace_country_select = Select(value=trace_country, title='Country to be traced', options=sorted(country_options))

widget_list = [year,indicator_x_select,indicator_y_select,indicator_z_select,area,trace_country_select]

#set updates for plot
for widget in widget_list:
	widget.on_change('value', update_data)

indicator_group_select.on_change('value',update_group)

#initialize plot
update_data(None,None,None)

# Set up layouts and add to document
inputs = VBoxForm(children=widget_list)
curdoc().add_root(HBox(children=[inputs, p]))


