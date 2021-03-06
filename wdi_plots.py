
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
from bokeh.models import HoverTool, ColumnDataSource, HBox, VBoxForm, Select, MultiSelect
from bokeh.models.widgets import Slider, Toggle, Button
from bokeh.io import curdoc

	
# ******  FUNCTIONS  ******
def load_Indicator(group_list):
	"""Load indicator dataframe for a group of indicators from SQL"""
	#create sql query string with all the indicator group names
	sql_query="SELECT * FROM Indicators WHERE IndicatorCode LIKE " + "'" +str(group_list[0]) + "%' "
	for group in group_list[1:]:
		sql_query+=str("OR IndicatorCode LIKE " + "'" +str(group) + "%' ")

	#load data
	indicator_df = pd.read_sql_query(sql_query, conn)
	indicator_name_df=indicator_df[['IndicatorCode', 'IndicatorName']].set_index('IndicatorName').drop_duplicates('IndicatorCode')

	#clean up of indicator_df
	indicator_df.set_index(['IndicatorCode','Year'], inplace = True, drop = True)
	indicator_df.drop(['CountryCode'], axis=1, inplace=True)
	indicator_df.dropna(inplace=True)

	return indicator_df, indicator_name_df

#TO BE REMOVED
def load_IndicatorOld(indicator_all, group_list):
	"""Load indicator dataframe for a group of indicators"""
	indicator_df = pd.DataFrame(); indicator_name_df = pd.DataFrame(); 
	#read all indicator groups from selection tool
	for group in group_list:
		indicator_df=indicator_df.append(indicator_all[indicator_all['IndicatorCode'].str.startswith(group)])
		indicator_name_df=indicator_name_df.append(indicator_df[['IndicatorCode', 'IndicatorName']].set_index('IndicatorName').drop_duplicates('IndicatorCode'))

	indicator_df.set_index(['IndicatorCode','Year'], inplace = True, drop = True)
	indicator_df.drop(['CountryCode'], axis=1, inplace=True)
	indicator_df.dropna(inplace=True)

	return indicator_df, indicator_name_df

def Indicator_group(str):
	'''given the start of an IndicatorCode this function returns all IndicatorNames of that subgroup of indicators'''
	return update_plot.indicator_df.loc[str].drop_duplicates('IndicatorName')	
	
def Ind_Name_f(Indicator_Code):
	'''generates IndicatorName from Code'''
	return update_plot.indicator_df.IndicatorName.loc[Indicator_Code].values.astype(str)[0]
	
def Ind_Code_f(Indicator_Name):
	'''returns IndicatorCode from Name'''
	return update_plot.indicator_name_df.loc[Indicator_Name].values.astype(str)[0]

#TO BE REMOVED
def axis_values(Indicator_Code, year, countries):
	"""get values for the Indicators for selected year and countries"""
	return update_plot.indicator_df.Value[(update_plot.indicator_df.IndicatorCode==Indicator_Code) & (update_plot.indicator_df.Year==year) & (update_plot.indicator_df.CountryName.isin(countries)) ]

#TO BE REMOVED
def time_and_values(Country_Name,Indicator_Code):
	'''generates values for Country_Name  and Indicator_Code indexed by the year'''
	data = pd.read_sql_query("SELECT Year,Value FROM Indicators WHERE CountryName=:x AND IndicatorCode=:y ",
	  conn, 
	  params={'x': Country_Name, 'y': Indicator_Code})
	# set index to year
	data.set_index('Year', inplace = True)
	return data

#TO BE REMOVED
def Indicator_finder(str):
	'''given a string lists the first 10 indictors that contain this string'''
	return pd.read_sql_query("SELECT * FROM Indicators WHERE IndicatorName LIKE @x GROUP BY IndicatorName LIMIT 10",
		conn,  params={'x': '%'+str +'%'})
#TO BE REMOVED
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

def display_error(message, visible, size='16pt', color='dimgrey'):
	"""print error (or loading) message tool screen. Use Visible=True/False to display or remove message"""
	#get text positon
	try:
		x=p.x_range.end/4; y=p.x_range.end/1.5
	except:
		x=[30]; y=[100]		#set defaults
		
	#update text glyph
	error_source.data = dict(
        x=[x],
        y=[y],
        text=[message],
        size=[size],
        color=[color]
    )
	#change visibility of error message
	error_message.glyph.visible=visible

# ******  CALLBACKS  ******
def update_group(attrname, old, new):
	"""update dataframe for selected inidcator group"""	

	display_error('loading new indicator group', True)		#display loading message
	
	update_plot.indicator_df, update_plot.indicator_name_df=load_Indicator(indicator_group_select.value)

	print("Indicator group {} loaded".format(indicator_group_select.value))

	indicator_options_x = tuple(update_plot.indicator_df.drop_duplicates('IndicatorName').IndicatorName.astype(str).values)  
	indicator_x_select.options=sorted(indicator_options_x)
	indicator_y_select.options=sorted(indicator_options_x)
	indicator_z_select.options=sorted(indicator_options_x)

	display_error('loading new indicator group', False)		#remove loading message
 
	#set update_group counter and call update_indicator
	update_group.counter=3
	update_indicator(None,None,None)

def update_group_check():
	"""check if group selection was updated and set the individual selectors (axis) iterativly"""
	if update_group.counter==0:
		pass

	elif update_group.counter==3:
		update_group.counter=2
		indicator_x_select.value=indicator_x_select.options[0]

	elif update_group.counter==2:
		update_group.counter=1
		indicator_y_select.value=indicator_y_select.options[0]

	elif update_group.counter==1:
		update_group.counter=0
		indicator_z_select.value=indicator_z_select.options[0]

def update_trace(attrname, old, new):
	"""update trace for plot and calls update plot"""
	if trace_toggle.active==True:
		update_plot.x_trace = update_plot.temp_ind_df.loc[trace_country_select.value]['x'].values
		update_plot.y_trace = update_plot.temp_ind_df.loc[trace_country_select.value]['y'].values
	else:
		update_plot.x_trace = []
		update_plot.y_trace = []
		update_plot.colors=[]; update_plot.alphas=[]
		for i in range(np.size(trace_country_select.options)):
   			update_plot.colors.append('steelblue')
   			update_plot.alphas.append(0.5)

	update_year(None,None,None)


def update_indicator(attrname, old, new):
	"""update indicator data for plot and calls update plot"""	
	#check if group selection has been changed
	update_group_check()
	
	#check the income and region group and selects the appropiate countries
	if country_income_select.value == 'All': 
		country_income_group = country_grp_data['TableName'].values
	else:
		country_income_group = country_grp_data.set_index('IncomeGroup').loc[country_income_select.value]['TableName'].values
		
	if country_region_select.value == 'All':
		country_region_group = country_grp_data['TableName'].values
	else:
		country_region_group = country_grp_data.set_index('Region').loc[country_region_select.value]['TableName'].values
		
	country_intersect = np.intersect1d(country_income_group,country_region_group)
	
	try:
		update_plot.temp_ind_df = pd.concat([
		update_plot.indicator_df.loc[Ind_Code_f(indicator_x_select.value),].set_index('CountryName', append = True).rename(columns={"Value": "x"}),
		update_plot.indicator_df.loc[Ind_Code_f(indicator_y_select.value),].set_index('CountryName', append = True).rename(columns={"Value": "y"}),
		update_plot.indicator_df.loc[Ind_Code_f(indicator_z_select.value),].set_index('CountryName', append = True).rename(columns={"Value": "z"})
		],axis = 1).dropna().reset_index().set_index('CountryName').loc[country_intersect]
			
		display_error('', False)		#remove error message if no error occured

	except KeyError as e:
		print( "Error: %s" % e )		#print error to shell
		display_error(e, True)		#display error message
		update_plot.temp_ind_df=pd.DataFrame(columns=[['x'],['y'],['y']])

	#set labels
	p.xaxis.axis_label = str(indicator_x_select.value)
	p.yaxis.axis_label = str(indicator_y_select.value)

	#get countries
	update_plot.countries=tuple(update_plot.temp_ind_df.index.drop_duplicates().values)
	trace_country_select.options=sorted(update_plot.countries)			#update countries selector

	#set year range for slider
	year.start=update_plot.temp_ind_df.Year.min()
	year.end=update_plot.temp_ind_df.Year.max()

	#set max range
	p.x_range.start = .5*update_plot.temp_ind_df['x'].min()
	p.x_range.end   = 1.1*update_plot.temp_ind_df['x'].max()
	p.y_range.start = .5*update_plot.temp_ind_df['y'].min()
	p.y_range.end   = 1.1*update_plot.temp_ind_df['y'].max()

	update_trace(None,None,None)


def update_year(attrname, old, new):
	"""update year of plot"""	
	update_plot.x=update_plot.temp_ind_df[update_plot.temp_ind_df.Year==year.value]['x'].values
	update_plot.y=update_plot.temp_ind_df[update_plot.temp_ind_df.Year==year.value]['y'].values

	#check for Z-toggle
	if z_toggle.active==True:
		update_plot.z=update_plot.temp_ind_df[update_plot.temp_ind_df.Year==year.value]['z'].values
		update_plot.z_normalisation = max(update_plot.z)
		p.title = ("Year=" +str(year.value)+ " -- Spot area ~" + str(indicator_z_select.value))
	else:
		update_plot.z=np.ones(np.size(update_plot.x)); update_plot.z_normalisation = 1
		p.title = ("Year=" +str(year.value))

	if trace_toggle.active==True:
		temp_countries=update_plot.temp_ind_df[update_plot.temp_ind_df.Year==year.value].reset_index().drop_duplicates('CountryName').CountryName
		index=temp_countries[temp_countries==trace_country_select.value].index.values[0]

		update_plot.colors=[]; update_plot.alphas=[]
		for i in range(np.size(temp_countries)):
   			update_plot.colors.append('steelblue')
   			update_plot.alphas.append(0.5)

		update_plot.colors[index]='red'
		update_plot.alphas[index]=1.0

	update_plot(None,None,None)	

def update_plot(attrname, old, new):
	"""update data for plot"""	

	source.data = dict(
        x=update_plot.x,
        y=update_plot.y,
        z=area.value*update_plot.z/update_plot.z_normalisation,
		x_trace = update_plot.x_trace,
		y_trace = update_plot.y_trace,
        countries=update_plot.countries,
        colors=update_plot.colors,
        alphas=update_plot.alphas
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
default_indicator_group=['SP']
update_plot.indicator_df, update_plot.indicator_name_df =load_Indicator(default_indicator_group)

#setting start values
Indicator_Code_x = 'SP.DYN.CBRT.IN'
Indicator_Code_y = 'SP.DYN.IMRT.IN'	 
Indicator_Code_z = 'SP.URB.TOTL.IN.ZS' 
Year_init		 =  2010
trace_country    = 'Swaziland'

#create figure
update_plot.colors=[]; update_plot.alphas=[]
hover = HoverTool( tooltips=[("Country", "@countries"), ('Area', "@z"), ("(x,y)", "(@x, @y)")] )
source = ColumnDataSource(data=dict(x=[], y=[],  z=[], x_trace=[], y_trace=[], countries=[], alphas=0.5, colors='steelblue'))

p = Figure(tools=[hover, "pan,box_zoom,reset,resize,save,wheel_zoom"])

p.scatter('x','y', radius='z', source=source, alpha='alphas', fill_color='colors')
p.line('x_trace','y_trace', source = source, line_width=4, line_alpha=0.7, line_color = 'darkorange')
p.title_text_font_size = '16pt'; p.title_text_align = 'left' # to ensure the year is displayed even for long names of the z-indicator

#setup error message
error_source=ColumnDataSource(data=dict(x=[30], y=[100], text=['Loading'],size=['16pt'], color=['dimgrey']))
error_message=p.text('x','y', text='text', text_font_size='size', text_color='color', visible=False, source=error_source)

#generate array of all countries and their region and income group
country_grp_data = pd.read_sql_query("SELECT * FROM Country ",  conn)[[u'TableName', u'Region', u'IncomeGroup']]

# generate selection options for the axis. VERY slow if the set of indicators is too large. For example 'SH' only takes forever.
indicator_options_x = tuple(update_plot.indicator_df.drop_duplicates('IndicatorName').IndicatorName.astype(str).values)  
indicator_options_y = tuple(update_plot.indicator_df.drop_duplicates('IndicatorName').IndicatorName.astype(str).values)  
indicator_options_z = tuple(update_plot.indicator_df.drop_duplicates('IndicatorName').IndicatorName.astype(str).values) 
country_options = tuple(update_plot.indicator_df.drop_duplicates('CountryName').CountryName.values.astype(str))
indicator_group_options = codes_unique_df['Group'].values.astype(str)
regions_options = ('South Asia', 'Europe & Central Asia', 'Middle East & North Africa', 'East Asia & Pacific',		
 	'Sub-Saharan Africa', 'Latin America & Caribbean', 'North America', 'All')
income_grps_options = ('Low income', 'Upper middle income', 'High income: nonOECD', 'Lower middle income', 'High income: OECD', 'All')

# Set up widgets
#sliders
year = Slider(title="Year", value=Year_init, start= 1960 , end=2015, step=1)
area = Slider(title="Spot Area", value=0.5, start= 0.05 , end=2.0, step=0.05)
#selectors
indicator_x_select = Select(value=Ind_Name_f(Indicator_Code_x), title='Indicator on x-axis', options=sorted(indicator_options_x))
indicator_y_select = Select(value=Ind_Name_f(Indicator_Code_y), title='Indicator on y-axis', options=sorted(indicator_options_y))
indicator_z_select = Select(value=Ind_Name_f(Indicator_Code_z), title='Indicator as spot area', options=sorted(indicator_options_z))
indicator_group_select = MultiSelect(value=default_indicator_group, title='Indicator group', options=sorted(indicator_group_options))
trace_country_select = Select(value=trace_country, title='Country to be traced', options=sorted(country_options))
country_region_select = Select(value = 'All', title = 'Geographic Region',options = sorted(regions_options))		
country_income_select = Select(value = 'All', title = 'Income group',options = sorted(income_grps_options))
#toggles
z_toggle=Toggle(label="Area", active=False,  type="primary")
trace_toggle=Toggle(label="Trace", active=False, type="primary")

widget_list = [year,indicator_x_select,indicator_y_select,indicator_z_select,area, trace_country_select, z_toggle, trace_toggle, indicator_group_select,country_region_select,country_income_select]

#set updates for plot
for widget in [indicator_x_select,indicator_y_select,indicator_z_select,country_region_select,country_income_select]:
	widget.on_change('value', update_indicator)
trace_country_select.on_change('value', update_trace)
indicator_group_select.on_change('value', update_group)

area.on_change('value', update_plot)
year.on_change('value', update_year)

trace_toggle.on_change('active', update_trace)
z_toggle.on_change('active', update_year)

# Set up layouts and add to document
inputs = VBoxForm(children=widget_list)
curdoc().add_root(HBox(children=[inputs, p]))

#initialize plot
update_group.counter=0
update_indicator(None,None,None)








