
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
	
def Indicator_Name_f(Indicator_Code):
	'''generates IndicatorName from Code'''
	return indicator_df.loc[Indicator_Code].IndicatorName.values.astype(str)[0]

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
def update_data(attrname, old, new):	
	x = indicator_df.loc[indicator_name_df.loc[indicator_x_select.value].values.astype(str)[0],year.value].Value.values
	y = indicator_df.loc[indicator_name_df.loc[indicator_y_select.value].values.astype(str)[0],year.value].Value.values
	z = indicator_df.loc[indicator_name_df.loc[indicator_z_select.value].values.astype(str)[0],year.value].Value.values
	z_normalisation = max(z)
	# updating the labels
	p.title = ("Year=" +str(year.value)+ " -- Spot area ~" + str(indicator_z_select.value)   )
	p.xaxis.axis_label = str(indicator_x_select.value)
	p.yaxis.axis_label = str(indicator_y_select.value)
	
	countries=pd.concat([indicator_df.loc[Indicator_Code_x,Year_1].CountryName,
	indicator_df.loc[Indicator_Code_y,Year_1].CountryName,
	indicator_df.loc[Indicator_Code_z,Year_1].CountryName]).drop_duplicates().astype(str).values

	source.data = dict(
        x=x,
        y=y,
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

#load all data
default_indicator_group='SH'
#indicator_all = pd.read_sql_query("SELECT * FROM Indicators",  conn)
#debugging set
indicator_all = pd.read_sql_query("SELECT * FROM Indicators WHERE IndicatorCode LIKE @x ", conn,  params={'x': '%'+ default_indicator_group+'%'})
indicator_df  = indicator_all[indicator_all['IndicatorCode'].str.startswith(default_indicator_group)]

print("data loaded")

#setting start values
Indicator_Code_x = 'SH.XPD.PUBL.ZS'  #Mortality rate, infant (per 1,000 live births)
Indicator_Code_y = 'SH.XPD.PUBL.ZS'	 #Health expenditure, public (% of GDP)
Indicator_Code_z = 'SH.XPD.PUBL.ZS'  #Birth rate, crude (per 1,000 people)

Year_1=2010

#get IndidcatorCorde and IndicatorName list
indicator_name_df=indicator_df[['IndicatorCode', 'IndicatorName']].set_index('IndicatorName').drop_duplicates('IndicatorCode')

#prepare indicator df
indicator_df.set_index(['IndicatorCode','Year'], inplace = True)
indicator_df.drop(['CountryCode'], axis=1, inplace=True)
indicator_df.dropna(inplace=True)

countries=pd.concat([indicator_df.loc[Indicator_Code_x,Year_1].CountryName,
	indicator_df.loc[Indicator_Code_y,Year_1].CountryName,
	indicator_df.loc[Indicator_Code_z,Year_1].CountryName]).drop_duplicates().astype(str).values

x = indicator_df.loc[Indicator_Code_x,Year_1].Value.values
y = indicator_df.loc[Indicator_Code_y,Year_1].Value.values
z = indicator_df.loc[Indicator_Code_z,Year_1].Value.values

z_normalisation = max(z)

#pack source data
source = ColumnDataSource(data=dict(
            x=x,
            y=y,
            countries=countries,
            z=0.5*z/z_normalisation
        )
    )

#create hover tooltips
hover = HoverTool(
        tooltips=[
            ("Country", "@countries"),
            ('Area', "@z"),
            ("(x,y)", "(@x, @y)"),
            ]
    )

#create figure
p = Figure(tools=[hover, "pan,box_zoom,reset,resize,save,wheel_zoom"])

# set title
p.title = (
	"Year=" +str(Year_1) # a linebreak would be good here, to fit all in the title
	+ " -- Spot area ~" + indicator_df.loc[Indicator_Code_z].IndicatorName.astype(str).values[0]   )
p.title_text_font_size = '16pt'
p.title_text_align = 'left' # to ensure the year is displayed even for long names of the z-indicator

#set labels
p.xaxis.axis_label = indicator_df.loc[Indicator_Code_x].IndicatorName.astype(str).values[0]
p.yaxis.axis_label = indicator_df.loc[Indicator_Code_y].IndicatorName.astype(str).values[0]

#plot
p.scatter('x','y', radius='z', source=source, alpha=.5)

# generate selection options for the axis. VERY slow if the set of indicators is too large. For example 'SH' only takes forever.
indicator_options_x = tuple(indicator_df.drop_duplicates('IndicatorName').IndicatorName.astype(str).values)  #default value is 'SH.XPD' for now
indicator_options_y = tuple(indicator_df.drop_duplicates('IndicatorName').IndicatorName.astype(str).values)  #default value is 'SP.DYN' for now
indicator_options_z = tuple(indicator_df.drop_duplicates('IndicatorName').IndicatorName.astype(str).values) #default value is 'SP.DYN' for now

# Set up widgets
year = Slider(title="Year", value=Year_1, start= 1990 , end=2015, step=1)
area = Slider(title="Spot Area", value=0.5, start= 0.05 , end=2.0, step=0.05)

indicator_x_select = Select(value=Indicator_Name_f(Indicator_Code_x), title='Indicator on x-axis', options=sorted(indicator_options_x))
indicator_y_select = Select(value=Indicator_Name_f(Indicator_Code_y), title='Indicator on y-axis', options=sorted(indicator_options_y))
indicator_z_select = Select(value=Indicator_Name_f(Indicator_Code_z), title='Indicator as spot area', options=sorted(indicator_options_z))

widget_list = [year,indicator_x_select,indicator_y_select,indicator_z_select,area ]

#set updates
for widget in widget_list:
	widget.on_change('value', update_data)


# Set up layouts and add to document
inputs = VBoxForm(children=[year,indicator_x_select,indicator_y_select,indicator_z_select,area])

curdoc().add_root(HBox(children=[inputs, p]))


