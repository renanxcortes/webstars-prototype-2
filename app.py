import pandas as pd
import numpy as np
from plotly import tools
import pysal as ps   
from libpysal.weights.contiguity import Queen
import giddy
from giddy import mobility
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output , State
from scipy import stats
from scipy.stats import rankdata
import geopandas as gpd
import base64 
import string
import math
import matplotlib.cm

# https://github.com/plotly/dash/issues/71
image_filename_stars = 'stars_logo.png'
encoded_image_stars = base64.b64encode(open(image_filename_stars, 'rb').read())

image_filename_plotly = 'plotly_logo.png'
encoded_image_plotly = base64.b64encode(open(image_filename_plotly, 'rb').read())

# For the more recent version of Dash with Tabs: pip install dash-core-components==0.24.0-rc2
# It was here https://github.com/plotly/dash-core-components/pull/213 andhttps://github.com/plotly/dash-core-components/pull/74

app = dash.Dash()
server = app.server
app.config['suppress_callback_exceptions']=True # If you have an id in the layout/callbacks that is not in the callbacks/layout

# Boostrap CSS.
app.css.append_css({'external_url': 'https://codepen.io/amyoshino/pen/jzXypZ.css'})  # noqa: E501


# Reading and Processing Data #

#### TIDY DATASET ###
csv_path = ps.examples.get_path('usjoin.csv')
usjoin = pd.read_csv(csv_path)

years = list(range(1929, 2010))                  
cols_to_calculate = list(map(str, years))

shp_path = ps.examples.get_path('us48.shp')
us48_map = gpd.read_file(shp_path)
us48_map = us48_map[['STATE_FIPS','STATE_ABBR','geometry']]
us48_map.STATE_FIPS = us48_map.STATE_FIPS.astype(int)
df_map = us48_map.merge(usjoin, on='STATE_FIPS')

# Making the dataset tidy
us_tidy = pd.melt(df_map, 
                  id_vars=['Name', 'STATE_FIPS', 'STATE_ABBR', 'geometry'],
                  value_vars=cols_to_calculate, 
                  var_name='Year', 
                  value_name='Income').sort_values('Name')

# Function that calculates Per Capita Ratio
def calculate_pcr(x):
    return x / np.mean(x)

# Establishing a contiguity matrix for a specific year. It is the same for all years.
W = Queen.from_dataframe(us_tidy[us_tidy.Year == '1929'])
W.transform = 'r'

# Function that calculates lagged value
def calculate_lag_value(x):
    return ps.lag_spatial(W, x)

# Function that calculates rank
def calculate_rank(x):
    return rankdata(x, method = 'ordinal')

# In the first function (calculate_pcr), a series is returned, in the second (calculate_lag_value), an array, so the assign method is used to keep the indexes of the pandas Dataframe

us_tidy['PCR'] = us_tidy.groupby('Year').Income.apply(lambda x: calculate_pcr(x))
us_tidy = us_tidy.assign(Rank = us_tidy.groupby('Year').Income.transform(calculate_rank),
                         Income_Lagged = us_tidy.groupby('Year').Income.transform(calculate_lag_value),
                         PCR_Lagged = us_tidy.groupby('Year').PCR.transform(calculate_lag_value))
#### END OF TIDY DATASET ###


first_year = int(min(us_tidy.Year))
last_year = int(max(us_tidy.Year))

years = list(range(first_year, last_year+1))                  
years_aux = [str(i) for i in years] # Converting each element to string (it could be list(map(str, years)))
years_options = [{'label': i, 'value': i} for i in years_aux]

 
step = 5
years_by_step = list(map(str, list(range(first_year, last_year + 1, step))))         

# For ranks dropdowns
ranks_aux = [str(i) for i in sorted(us_tidy.Rank.unique())] # Converting each element to string (it could be list(map(str, years)))
ranks_options = [{'label': i + 'th', 'value': i} for i in ranks_aux]
ranks_options[0]['label'] = '1st'
ranks_options[1]['label'] = '2nd'
ranks_options[2]['label'] = '3rd'



# For Global Moran`s I
W = Queen.from_dataframe(us_tidy[us_tidy.Year == str(first_year)])
W.transform = 'r'
morans = us_tidy.groupby('Year').Income.apply(lambda x: ps.Moran(x, W).I).tolist()





'''
~~~~~~~~~~~~~~~~
~~ APP LAYOUT ~~
~~~~~~~~~~~~~~~~
''' 
app.layout = html.Div(
        html.Div([    
        html.Div([
                    
                    html.H1(children='Web STARS', style={'textAlign': 'center'}),
                    
                    html.H2(children='A web-based version of Space-Time Analysis of Regional Systems',
                            style={'textAlign': 'center'}),
                
                
                dcc.Tabs(id="main_tabs", style = {'textAlign': 'center', 
                                     'backgroundColor':'lightblue',
                                     #'width': '75%'
                                     },
                children=[
        
                dcc.Tab(label='Presentation', style={'font-weight': 'bold', 'font-size': '120%'}, children=[
                        
                html.H3(children='This is a beta-version of some functions of STARS using Dash from plotly.', 
                style={'textAlign': 'center',
                   'margin-top': '60', 
                   'font-size': '110%'}),
    
                dcc.Upload(
                    id='upload-csv',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select'), ' comma separated value (.csv)'
                    ]),
                    style={
                        'width': '25%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px',
                        'margin-left': 600,
                        'margin-right': 600
                    },
                    # Allow multiple files to be uploaded?
                    multiple=False
                    ),
    
                
                    dcc.Upload(
                    id='upload-shp',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select'), ' shapefile (.shp)'
                    ]),
                    style={
                        'width': '25%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px',
                        'margin-left': 600,
                        'margin-right': 600
                    },
                    # Allow multiple files to be uploaded?
                    multiple=False
                    ),
    
                html.Img(src='data:image/png;base64,{}'.format(encoded_image_stars.decode()), 
                 style={'width': '150px',
                'margin-left': 700}),
                
                html.Img(src='data:image/png;base64,{}'.format(encoded_image_plotly.decode()), 
                 style={'width': '150px',
                'margin-left': 700}) 
                        
                        ]),
        
        
                dcc.Tab(label='ESDA', style={'font-weight': 'bold', 'font-size': '120%'}, children=[
               
                html.Div([
                        html.P('Select the Year:', style={'margin-top': '5', 
                                                          'font-size': '150%', 
                                                          'font-weight': 'bold',
                                                          'textAlign': 'center'}),
                        dcc.Slider(
                            id='years-slider',
                            min=min(years),
                            max=max(years),
                            value=min(years),
                            marks={str(year): str(year) for year in years_by_step}
                        ),                        
                        dcc.Interval(
                            id='interval-event',
                            interval=24*60*60*1000,
                            n_intervals=0
                        ),
                    
                html.P('Select the Variable to analyze:', style={'margin-top': '35', 'font-size': '150%', 'font-weight': 'bold'}),    
                dcc.RadioItems(
                            id='type_data_selector',
                            options=[
                                {'label': 'Per Capita Relative Ratio (PCR)', 'value': 'pcr'},
                                {'label': 'Raw Income Data', 'value': 'raw'}
                            ],
                            value='pcr',

                            style={'margin-top': '0', 'font-size': '125%'}
                    ),
                    
               html.Div([ 
               html.P('Animation:', style={'margin-top': '20', 'font-size': '150%', 'font-weight': 'bold'})
               ]),
               
               html.Div([
               dcc.Checklist(
                            id='auto-check',
                            options=[{'label': ' Time Travelling ', 'value': 'auto'}],
                            values=[],
                        )]),  
                        
                
                html.Div([
                dcc.Checklist(
                id='spatial_travel-check',
                options=[{'label': ' Spatial Travelling ', 'value': 'auto'}],
                values=[],
                )]),
                
                dcc.Interval(
                    id='spatial_interval-event',
                    interval=24*60*60*1000,
                    n_intervals=0
                ),
                                
                        ], style={'width':1350, 'margin':25, 'float': 'left'}),
                
                html.Div([            
            html.Div([
                        
                            dcc.Graph(
                                id='choropleth-graph'
                            ),
                        
                            dcc.Graph( # ?dcc.Graph to learn more about the properties
                                id='timeseries-graph',
                            clear_on_unhover = 'True' # Sets the slider year when the mouse hover if off the graph
                            ),    
                        
                            # dcc.Graph(
                            #    id='timepath-graph'
                            #),
                                    
                    ], className="four columns"),        
            html.Div([                
                        
                        dcc.Graph(
                                id='scatter-graph'
                            ),
                        
                            html.P('Change the years below:'),
                                
                            dcc.Graph(
                                id='density-graph' 
                            ),
                                               
                            html.P('Choose a pair of years for densities:', style = {'font-weight': 'bold'}),
                            
                            html.Div([
                            dcc.Dropdown(
                                id='initial_years_dropdown',
                                options=years_options,
                                value=str(first_year)
                            ),
                            dcc.Dropdown(
                                id='final_years_dropdown',
                                options=years_options,
                                value=str(last_year)
                            )], className="row"),
                                           
                        
                    ], className="four columns"),        
            html.Div([
                            dcc.Graph(
                                id='timepath-graph'
                            ),
                             dcc.Graph(
                                id='boxplot-graph'
                            ),           
					 ], className="four columns"),    
        ], className="row", style={'width': '100%', 'display': 'inline-block', 'float': 'center'}) ]),
        
        
        dcc.Tab(label='Rank Paths', style={'font-weight': 'bold', 'font-size': '120%'}, children=[
                
                
            html.Div([
            html.P('Select the Rank for the Path:', style = {'font-size': '150%', 'margin-top':25, 'font-weight': 'bold'}),
            
            html.Div([
            dcc.Dropdown(
                            id='rankpath_dropdown',
                            options=ranks_options,
                            value='1'
                        )], style = {'margin-left':600,
                                     'margin-right':600,
                                     'margin-top':10}),
            
            html.Div([
                html.P('Year Highlighted:', style={'margin-top': '25', 'font-size': '150%', 'font-weight': 'bold'}), 
                dcc.Slider(
                            id='years-slider-rank-path',
                            min=min(years),
                            max=max(years),
                            value=min(years),
                            marks={str(year): str(year) for year in years_by_step}
                        )
                ], style={'width': '75%', 
                          'margin-left':50,
                          'margin-right':50,
                          'textAlign': 'center',
                          'display':'inline-block'}),
                    
            html.Div([                           
            dcc.Graph(
                                id='rank-path-graph'
                                
                            )], style = {'margin-left':185,
                                         'margin-right':150,
                                         'margin-top':25})
                    

            
        ], className="twelve columns", style={#'width': '75%',
                                              'textAlign': 'center', 
                                              #'margin-left':150,
                                              #'margin-top':20,
                                              'backgroundColor':'rgb(244, 244, 255)'}) # Or 'lightgray' or look here https://www.w3schools.com/colors/colors_rgb.asp 
                
                
                ]),
        
        
        dcc.Tab(label='Giddy', style={'font-weight': 'bold', 'font-size': '120%'}, children=[
                
                dcc.Tabs(id="giddy_tabs", style = {'textAlign': 'center', 
                                     'backgroundColor':'lightblue',
                                     #'width': '75%'
                                     },
                vertical = True,
                children=[
        
                dcc.Tab(label='Directional LISA (Rose)', style={'font-weight': 'bold', 'font-size': '120%'}, children=[
                        
                html.Div([
                        
                        html.P('Select the pair of years below:', style = {'font-size': '150%', 
                                                                           'margin-top':25,
                                                                           'margin-bottom':25,
                                                                           'font-weight': 'bold', 
                                                                           'margin-left':500, 
                                                                           'margin-right':500}),
                
                html.Div([
                        dcc.RangeSlider(
                        id='rose-range-slider',
                        min = first_year,
                        max = last_year,
                        step = 1,
                        marks = {str(year): str(year) for year in years_by_step},
                        value = [first_year, last_year]                        
                                )], style = {'margin-bottom':60, 'margin-left':50, 'margin-right':50}),
                        
                html.Div([
                        
                html.P('Circular sectors in diagram (k):', style = {'font-size': '150%', 'margin-top':25, 'font-weight': 'bold'}),
                
                dcc.Dropdown(
                                id='rose-k',
                                options = [{'label': i, 'value': i} for i in list(range(1, 51))],
                                value = 30
                                )], style = {'margin-left':550,
                                         'margin-right':550,
                                         'margin-bottom':25,
                                         'margin-top':25}),
            
            
                html.Div([
                        dcc.Graph(
                                id='rose-graph'
                                
                            )], style={'width':600, 'margin-left':400, 'margin-right':400})])

                ]),
            
                dcc.Tab(label='Markov Methods and Mobility Measures', style={'font-weight': 'bold', 'font-size': '120%'}, children=[
                
                
                html.Div([
                html.P('Select the number of classes (quantiles):', style = {'font-size': '150%', 'margin-top':25, 'font-weight': 'bold'}),
                
                html.Div([
                dcc.Dropdown(
                                id='markov-pooled-classes-dropdown',
                                options = [{'label': i, 'value': i} for i in range(1, 10)],
                                value = 5
                                ),
                        
                html.P('Select the number of spatial lags:', style = {'font-size': '150%', 'margin-top':25, 'font-weight': 'bold'}),
                
                dcc.Dropdown(
                                id='markov-pooled-spatial-dropdown',
                                options = [{'label': i, 'value': i} for i in [3, 6, 9]],
                                value = 3
                                )], style = {'margin-left':500,
                                         'margin-right':500,
                                         'margin-top':10}),
                        
                html.Div([                           
                dcc.Graph(id='markov-pooled-graph')], style = {'margin-left':185,
                                             'margin-right':150,
                                             'margin-top':25}),
                        
                
                html.Div([                           
                dcc.Graph(id='markov-spatial-graph')], style = {'margin-left':185,
                                             'margin-right':150,
                                             'margin-top':25})
                        
    
                
                ], className="twelve columns", style={#'width': '75%',
                                                  'textAlign': 'center', 
                                                  #'margin-left':150,
                                                  #'margin-top':20,
                                                  'backgroundColor':'rgb(244, 244, 255)'})
                            
                ]),
            
            
                dcc.Tab(label='Rank Methods', style={'font-weight': 'bold', 'font-size': '120%'}, children=[
                        
                html.Div([
                        
                        html.P('Select the pair of years below:', style = {'font-size': '150%', 
                                                                           'margin-top':25,
                                                                           'margin-bottom':25,
                                                                           'font-weight': 'bold', 
                                                                           'margin-left':500, 
                                                                           'margin-right':500}),
                
                html.Div([
                        dcc.RangeSlider(
                        id='rank-range-slider',
                        min = first_year,
                        max = last_year,
                        step = 1,
                        marks = {str(year): str(year) for year in years_by_step},
                        value = [first_year, last_year]                        
                                )], style = {'margin-bottom':60}),
                        
                        
                        dcc.Graph(
                                id='lima-neighborhood-graph'
                                
                            )], style={'width':1350, 
                                       'margin':25, 
                                       'float': 'left'}),
                                
                
                        
                ]),
            
                dcc.Tab(label='Miscellaneous', style={'font-weight': 'bold', 'font-size': '120%'}, children=[
                        
                html.H3(children='Put here other features from Giddy.', 
                style={'textAlign': 'center',
                   'margin-top': '60', 
                   'font-size': '110%'}),
    
                html.Img(src='data:image/png;base64,{}'.format(encoded_image_stars.decode()), 
                 style={'width': '150px',
                'margin-left': 700}),
                
                html.Img(src='data:image/png;base64,{}'.format(encoded_image_plotly.decode()), 
                 style={'width': '150px',
                'margin-left': 700}) 
                        
                ])
            
                ])
                
                ])
        
        
        
        ])
        ])
    ], className='ten columns offset-by-one', 
       style = {'backgroundColor':'rgb(244, 244, 255)'})
)




############################################################ 
@app.callback(
    Output('interval-event', 'interval'), 
    [Input('auto-check', 'values')],
    [State('interval-event', 'interval')]
)
def change_auto(checkedValues, interval):
    #print(checkedValues, interval)
    if (len(checkedValues) != 0): return 2*1000                      # AUTO is checked
    else:                         return 24*60*60*1000               # AUTO is not checked


#@app.callback(Output('years-slider', 'value'), [Input('interval-event', 'n_intervals')], events=[Event('interval-event', 'interval')])
@app.callback(
    Output('years-slider', 'value'), 
    [Input('interval-event', 'n_intervals')],
    [State('years-slider', 'value'), State('years-slider', 'min'), State('years-slider', 'max'), State('auto-check', 'values')]
)
def update_slider(n, theYear, minValue, maxValue, checkedValues):
    if (len(checkedValues) == 0): return theYear                     # AUTO is not checked
    newValue = theYear + 1
    if (newValue > maxValue): newValue = minValue
    #print(n, theYear, minValue, maxValue, newValue, checkedValues)
    return newValue


# hide the options of the spatial_travel-check when AUTO is checked
@app.callback(
    Output('spatial_travel-check', 'options'), 
    [Input('auto-check', 'values')],
)
def hide_show_spatial_travel_checkbox(checkedValues):
    print(checkedValues)
    if (len(checkedValues) != 0): return []                                    # AUTO is checked
    else: return [{'label': ' Spatial Travelling ', 'value': 'auto'}]    # AUTO is not checked

# clear the values of the spatial_travel-check when AUTO is checked or not
@app.callback(
    Output('spatial_travel-check', 'values'), 
    [Input('auto-check', 'values')],
)
def clear_values_of_spatial_travel_checkbox(checkedValues):
    #print(checkedValues)
    return []

# reset n_intervals in the Sspatial_interval-event when AUTO is checked or not
# reset n_intervals in the Sspatial_interval-event when year is changed in the years-slider
@app.callback(
    Output('spatial_interval-event', 'n_intervals'), 
    [Input('auto-check', 'values'), Input('years-slider','value')],
    [State('spatial_interval-event', 'n_intervals')],
)
def reset_n_intervals_of_spatial_interval_event(checkedValues, year, oldValue):
    #print(checkedValues, 'oldValue:', oldValue)
    return 0

# set the spatial_interval-event using the Spatial Travel Animation check box
@app.callback(
    Output('spatial_interval-event', 'interval'), 
    [Input('spatial_travel-check', 'values')],
    [State('spatial_interval-event', 'interval'), State('spatial_interval-event', 'n_intervals')]
)
def change_spatial_travel_interval(checkedValues, interval, n):
    print(checkedValues, interval, n)
    if (len(checkedValues) != 0): return 2*1000                      # AUTO is checked
    else:                         return 24*60*60*1000               # AUTO is not checked

############################################################ 



############################################################

@app.callback(
    Output('choropleth-graph', 'figure'),
    [Input('type_data_selector', 'value'),
     Input('timeseries-graph','hoverData'), #'clickData'),
     Input('years-slider','value'), 
     Input('spatial_interval-event', 'n_intervals')],
    [State('spatial_travel-check', 'values')],
)
def update_map(type_data, year_hovered, year_selected_slider, n, checkedValues):
    
    if type_data == 'raw': 
        df_map = us_tidy[['Name','STATE_ABBR','Year','Income']].\
                 pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'Income').\
                 reset_index().\
                 merge(us48_map, on='STATE_ABBR')                 
        title_map = '(Raw)'
    
    else:
        df_map = us_tidy[['Name','STATE_ABBR','Year','PCR']].\
                 pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'PCR').\
                 reset_index().\
                 merge(us48_map, on='STATE_ABBR')
        title_map = '(PCR)'
    
    rk_map = us_tidy[['Name','STATE_ABBR','Year','Rank']].\
             pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'Rank').\
             reset_index().\
             merge(us48_map, on='STATE_ABBR')
    
    if year_hovered is None: 
        year = year_selected_slider
    
    else:
        year = year_hovered['points'][0]['x']

    heading = 'Income of US by State in ' + str(year)
    ranking = -1
    if (len(checkedValues) != 0):
        ranking = n % len(df_map[str(year)]) #+ 1
        msg = str(ranking) + 'th'
        if (ranking == 1): msg = '1st'
        if (ranking == 2): msg = '2nd'
        if (ranking == 3): msg = '3rd'
        for i, rank in enumerate(rk_map[str(year)]):
            if (rank == ranking): msg += ' ' + rk_map['Name'][i] + ': {0:.2f}'.format(df_map[str(year)][i])
        heading += '<br>(' + msg + ')'
    
    scl  = [[0.0, '#eff3ff'],[0.2, '#c6dbef'],[0.4, '#9ecae1'],[0.6, '#6baed6'],[0.8, '#3182bd'],[1.0, '#08519c']]
    scl2 = [[0.0, '#ffffff'],[1.0, '#FFFF00']]

    Choropleth_Data = [ dict(
                        type='choropleth',
                        colorscale = scl,
                        autocolorscale = False,
                        locations = df_map['STATE_ABBR'],
                        z = df_map[str(year)],
                        locationmode = 'USA-states',
                        text = df_map['Name'],
                        marker = dict(
                            line = dict (
                                color = 'rgb(255,255,255)',
                                width = 1
                            ) ),
                        colorbar = dict(
                            thickness = 10,
                            title = title_map)
                        ) ]
        
    Choropleth_Layout =  dict(
                            title = heading,
                            geo = dict(
                            scope='usa',
                            projection=dict( type='albers usa' ),
                            showlakes = True,
                            lakecolor = 'rgb(255, 255, 255)'),
                        )
    Choropleth = {
        'data': Choropleth_Data,
        'layout': Choropleth_Layout
    }

    if (ranking > 0):
        Choropleth_highlighted = [ dict(
                        type='choropleth',
                        colorscale = scl2,
                        autocolorscale = False,
                        locations = df_map['STATE_ABBR'],
                        z = [1 if i == ranking else 0 for i in rk_map[str(year)]],
                        showscale = False,
                        locationmode = 'USA-states',
                        text = df_map['Name'],
                        marker = dict(
                            opacity = 0.5,
                            line = dict (
                                color = 'rgb(255,255,255)',
                                width = 0
                            ) ),
                        ) ]
        Choropleth = {
            'data': Choropleth_Data + Choropleth_highlighted,
            'layout': Choropleth_Layout
        }

    return Choropleth

############################################################

# https://dash.plot.ly/interactive-graphing

@app.callback(
    Output('scatter-graph', 'figure'),
    [Input('type_data_selector', 'value'),
     Input('timeseries-graph','hoverData'),#'clickData'),
     Input('years-slider','value'),
     Input('choropleth-graph','selectedData'),
     Input('scatter-graph','selectedData'),
     Input('choropleth-graph','clickData')])
def update_scatter(type_data, year_hovered, year_selected_slider, 
                  states_selected_choropleth, states_selected_scatter, state_clicked_choropleth):
    
    if type_data == 'raw': 
        df_map = us_tidy[['Name','STATE_ABBR','Year','Income']].\
                 pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'Income').\
                 reset_index().\
                 merge(us48_map, on='STATE_ABBR')  
    
    else:
        df_map = us_tidy[['Name','STATE_ABBR','Year','PCR']].\
                 pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'PCR').\
                 reset_index().\
                 merge(us48_map, on='STATE_ABBR')
        
    if year_hovered is None: 
        year = year_selected_slider
    
    else:
        year = year_hovered['points'][0]['x']
    
    if ((states_selected_choropleth is None) & (state_clicked_choropleth is None)):
        state_selected = ['California']
        title_graph = state_selected[0]
    
    elif ((states_selected_choropleth is None) & (state_clicked_choropleth is not None)):
        state_selected = [str(state_clicked_choropleth['points'][0]['text'])]
        title_graph = state_selected[0]
    
    else:
        state_selected = [i['text'] for i in states_selected_choropleth['points']]# state_selected_choropleth['points'][0]['text']
        title_graph = 'Multiple States'
    
    VarLag = ps.lag_spatial(W, df_map[str(year)])
    Var = df_map[str(year)]

    states = np.array(df_map['Name'])
    colors = np.where(np.isin(states, state_selected), '#FF0066', '#0066FF')
    
    b,a = np.polyfit(Var, VarLag, 1)
    line0 = { 'x':[min(Var), max(Var)], 'y': [a + i * b for i in [min(Var), max(Var)]] }

    Scatter_Data = [
                        {
                            'x': Var, 
                            'y': VarLag,
                            'mode': 'markers',
                            'marker': {'size': 10,
                                       'color': colors},
                            'name': str(year),
                        'text': df_map['Name']},
                        {
                            'x': line0['x'], 
                            'y': line0['y'],
                            'mode': 'lines',
                            'line': {'color': '#009999'},
                            'name': 'Reg'}
    ]
    
    var = []
    varLag = []
    if (states_selected_choropleth is not None and
        'points' in states_selected_choropleth and len(states_selected_choropleth['points']) >= 2):
        var = [v['z'] for v in states_selected_choropleth['points']]
        varLag = [VarLag[v['pointIndex']] for v in states_selected_choropleth['points']]
    if (states_selected_scatter is not None and
        'points' in states_selected_scatter and len(states_selected_scatter['points']) >= 2):
        var = [v['x'] for v in states_selected_scatter['points']]
        #varLag = [VarLag[v['pointIndex']] for v in states_selected_scatter['points']]
        varLag = [v['y'] for v in states_selected_scatter['points']]
        
    if (len(var) != 0 and len(varLag) != 0):
        b,a = np.polyfit(var, varLag, 1)
        line1 = { 'x':[min(Var), max(Var)], 'y': [a + i * b for i in [min(Var), max(Var)]] }
        line2 = { 'x':[min(var), max(var)], 'y': [a + i * b for i in [min(var), max(var)]] }

        # recalculation line1 to fit scatter-graph area                                  # y = a * x + b
        minVar = min(Var)
        maxVar = max(Var)
        aa = (line1['y'][1] - line1['y'][0]) / (line1['x'][1] - line1['x'][0])
        bb = line1['y'][0] - aa * line1['x'][0]
        if (line1['y'][0] > max(VarLag)): minVar = (max(VarLag) - bb) / aa               # x = ( y - b ) / a
        if (line1['y'][0] < min(VarLag)): minVar = (min(VarLag) - bb) / aa               # x = ( y - b ) / a
        if (line1['y'][1] > max(VarLag)): maxVar = (max(VarLag) - bb) / aa               # x = ( y - b ) / a
        if (line1['y'][1] < min(VarLag)): maxVar = (min(VarLag) - bb) / aa               # x = ( y - b ) / a
        line1 = { 'x':[minVar, maxVar], 'y': [a + i * b for i in [minVar, maxVar]] }

        #print(var)
        Scatter_Data.append(
        	{
        		'x': line1['x'], 
                'y': line1['y'],
                'mode': 'lines', 
                'line': {'color': '#FF6600'},
                #'line': {'color': '#0000FF'},
                'name': 'Reg'}
        )
        Scatter_Data.append(
        	{
        		'x': line2['x'], 
                'y': line2['y'],
                'mode': 'lines', 
                'line': {'color': '#FF0000'},
                'name': 'Reg'}
        )
    
    Scatter_Layout = {
                        'xaxis': {'title': 'Original Variable'},
                        'yaxis': {'title': "Lagged Variable"},
                     'showlegend': False,
                     'title': 'Scatterplot for {} <br>{} highlighted'.format(year, title_graph)
                     }
    
    Scatter = {
        'data': Scatter_Data,
        'layout': Scatter_Layout
    }
    return Scatter

############################################################
    

############################################################
    

@app.callback(
    Output('timeseries-graph', 'figure'),
    [Input('timeseries-graph','hoverData'),#'clickData'),
    Input('years-slider', 'value')],
    [State('years-slider', 'min')]
)

def update_TimeSeries(year_hovered, year_selected_slider, minValue):
    
    if year_hovered is None:    
        theIDX = year_selected_slider - minValue
    
    else:
        theIDX = year_hovered['points'][0]['x'] - minValue    
    
    TimeSeries_Data = [
        {
            'x': years, 
            'y': morans,
            'mode': 'lines', 
            'name': 'Moran\'s I'
        },
        {
            'x': [years[theIDX]], 
            'y': [morans[theIDX]],
            'mode': 'markers', 
            'marker': {'size': 10},
            'name': 'Moran\'s I',
            'showlegend': False,
            'hoverinfo': 'none'
        } # To supress the tooltip
    ]    

    TimeSeries_Choropleth_Layout = {
        'xaxis': {'title': 'Years'},
        'yaxis': {'title': "Moran's I"}
    }
            
    TimeSeries = {
        'data': TimeSeries_Data,
        'layout': TimeSeries_Choropleth_Layout
    }
             
    return TimeSeries


#################################################################



@app.callback(
    Output('boxplot-graph', 'figure'),
    [Input('type_data_selector', 'value'),
     Input('timeseries-graph','hoverData'),#'clickData'),
     Input('choropleth-graph','selectedData'),
     Input('scatter-graph','selectedData'),
     Input('years-slider','value')])
def update_boxplot(type_data, year_hovered, states_selected_choropleth, states_selected_scatter, year_selected_slider):
    
    if type_data == 'raw': 
        df_map = us_tidy[['Name','STATE_ABBR','Year','Income']].\
                 pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'Income').\
                 reset_index().\
                 merge(us48_map, on='STATE_ABBR')  
    
    else:
        df_map = us_tidy[['Name','STATE_ABBR','Year','PCR']].\
                 pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'PCR').\
                 reset_index().\
                 merge(us48_map, on='STATE_ABBR')  

    selected = []
    
    if ((states_selected_choropleth is not None)):
        selected = [i['pointIndex'] for i in states_selected_choropleth['points']]
    if ((states_selected_scatter is not None)):
        selected = [i['pointIndex'] for i in states_selected_scatter['points']]
    
    if year_hovered is None: 
        year = year_selected_slider
    
    else:
        year = year_hovered['points'][0]['x']

    #states = np.array(df_map['Name'])
    #colors = np.where(np.isin(states, state_selected), '#FF0066', '#0066FF')
        
    trace0 = dict(
        type = 'box',
        y = df_map[str(year)],
        name = 'Boxplot of the variable',
        boxpoints='all',                                             # Show the underlying point of the boxplot
        jitter=0.15,                                                 # Degree of fuzziness
        pointpos=0,                                                  # Adjust horizontal location of point
        #marker = dict(color = '#FF0066'),
        line = dict(color = '#444'),
        selected = dict(marker = dict(color = '#FF0066')),
        unselected = dict(marker = dict(color = '#0066FF', opacity = 1.0)),
        selectedpoints = selected,
    )
    BoxPlot_Data = [trace0]
    #print(BoxPlot_Data)
    
    BoxPlot = {
                'data': BoxPlot_Data,
                'layout': {'title': 'Boxplot of the year {}'.format(str(year))}
              } 
    return BoxPlot

 


############################################################


@app.callback(
    Output('timepath-graph', 'figure'),
    [Input('type_data_selector', 'value'),
     Input('choropleth-graph','clickData'),
     Input('timeseries-graph','hoverData'),
     Input('years-slider', 'value')],
     [State('years-slider', 'min')])
def update_timepath(type_data, state_clicked_choropleth, year_hovered, year_selected_slider, minValue): # , state_clicked_scatter
    
    if type_data == 'raw': 
        df_map = us_tidy[['Name','STATE_ABBR','Year','Income']].\
                 pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'Income').\
                 reset_index().\
                 merge(us48_map, on='STATE_ABBR')
    
    else:
        df_map = us_tidy[['Name','STATE_ABBR','Year','PCR']].\
                 pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'PCR').\
                 reset_index().\
                 merge(us48_map, on='STATE_ABBR')
            
    if (state_clicked_choropleth is None):
        state_selected = 'California'
    
    if (state_clicked_choropleth is not None):
        state_selected = str(state_clicked_choropleth['points'][0]['text'])
    
    
    if year_hovered is None:    
        theIDX = year_selected_slider - minValue
    
    else:
        theIDX = year_hovered['points'][0]['x'] - minValue
    
    if year_hovered is None:    
        year = year_selected_slider
    
    else:
        year = year_hovered['points'][0]['x']
    
    def calculate_lag_value(x):
        return ps.lag_spatial(W, x)
    
    all_lagged = df_map[cols_to_calculate].apply(calculate_lag_value)
    
    state_row_index = list(df_map['Name']).index(state_selected)
    
    VarLag = all_lagged.iloc[state_row_index,:]
    Var = df_map[cols_to_calculate].iloc[state_row_index,:]
    
    TimePath_Data = [
                        {
                            'x': Var[[theIDX]], 
                            'y': VarLag[[theIDX]],
                            'mode': 'markers',
                            'marker': {'size': 12},
                            'name': '',
                        'text': str(year)},
                        {
                            'x': Var, 
                            'y': VarLag,
                            'mode': 'lines', 
                            'name': 'Path',
                        'hoverinfo': 'none'}
                    ]
    
    TimePath_Layout = {
                        'xaxis': {'title': 'Original Variable'},
                        'yaxis': {'title': "Lagged Variable"},
                     'showlegend': False,
                     'title': 'Time-path for {}<br> Highlighted {}'.format(str(state_selected), str(year))
                     }
    
    TimePath = {
        'data': TimePath_Data,
        'layout': TimePath_Layout
    }
    return TimePath

############################################################ 




@app.callback(
    Output('density-graph', 'figure'),
    [Input('type_data_selector', 'value'),
     Input('initial_years_dropdown','value'),
     Input('final_years_dropdown','value'),
     Input('choropleth-graph','clickData'),
     Input('spatial_interval-event', 'n_intervals')],
     [State('spatial_travel-check', 'values')])
def update_density(type_data, initial_year, final_year, state_clicked_choropleth, n, checkedValues): # , state_clicked_scatter
    
    if type_data == 'raw': 
        df_map = us_tidy[['Name','STATE_ABBR','Year','Income']].\
                 pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'Income').\
                 reset_index().\
                 merge(us48_map, on='STATE_ABBR')
    
    else:
        df_map = us_tidy[['Name','STATE_ABBR','Year','PCR']].\
                 pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'PCR').\
                 reset_index().\
                 merge(us48_map, on='STATE_ABBR')
        
    rk_map = us_tidy[['Name','STATE_ABBR','Year','Rank']].\
         pivot_table(index = ['Name','STATE_ABBR'], columns = 'Year', values = 'Rank').\
         reset_index().\
         merge(us48_map, on='STATE_ABBR')
    
    pair_of_years = [initial_year, final_year]
    
    
    if (state_clicked_choropleth is None): 
        chosen_state = 'California'
    
    if (state_clicked_choropleth is not None):
        chosen_state = str(state_clicked_choropleth['points'][0]['text'])
   
    ranking = -1
    if (len(checkedValues) != 0):
    	ranking = n % len(df_map[str(year)]) + 1
        
    else:
       ranking = rk_map.loc[list(df_map['Name']).index(chosen_state), initial_year]
    
    state_row_index = list(rk_map[initial_year]).index(ranking)
    
    initial_state_value = df_map[initial_year][state_row_index]
    final_state_value = df_map[final_year][state_row_index]
        
    X1 = np.array(df_map[pair_of_years[0]])
    X2 = np.array(df_map[pair_of_years[1]])
    
    kde1 = stats.gaussian_kde(X1, bw_method = 'silverman')
    kde2 = stats.gaussian_kde(X2, bw_method = 'silverman')
    
    # Joint grid
    min_grid_aux = min(np.concatenate([X1, X2]))
    max_grid_aux = max(np.concatenate([X1, X2]))
    X_grid = np.linspace(min_grid_aux - 0.1 * abs(max_grid_aux), 
                         max_grid_aux + 0.1 * abs(max_grid_aux), 
                         10000)
    
    dens1 = kde1.evaluate(X_grid)
    dens2 = kde2.evaluate(X_grid)
    
    Density_Data = [  # Densities traces
                        {
                            'x': X_grid, 
                            'y': dens1,
                            'mode': 'lines',
                         'fill': 'tozeroy',
                            'name': initial_year,
                        'text': 'Year of {}'.format(initial_year),
                        'line': {'color': '#AAAAFF',
                                 'width': 3}},
                          {
                            'x': X_grid, 
                            'y': dens2,
                            'mode': 'lines',
                         'fill': 'tozeroy',
                            'name': final_year,
                        'text': 'Year of {}'.format(final_year),
                        'line': {'color': '#FF0000',
                                 'width': 3}},
            
            
                     # Segments of lines traces
                     {
                            'x': [initial_state_value, initial_state_value], # x-values of each point do draw a line
                            'y': [0, kde1.evaluate(initial_state_value)[0]], # Extract only the value from an array: https://stackoverflow.com/questions/21030621/how-to-extract-value-from-a-numpy-ndarray
                            'mode': 'lines',
                            'name': 'name_to_put',
                        'text': 'text_to_put_line',
                        'showlegend': False,
                        'line': {'color': '#AAAAFF',
                                 'width': 3}},
                     {
                            'x': [final_state_value, final_state_value], # x-values of each point do draw a line
                            'y': [0, kde2.evaluate(final_state_value)[0]],
                            'mode': 'lines',
                            'name': 'name_to_put_line',
                        'text': 'text_to_put_line',
                        'showlegend': False,
                        'line': {'color': '#FF0000',
                                 'width': 3}}
                          
                    ]
    
    Density_Layout = {
                        'xaxis': {'title': 'Original Variable'},
                        'yaxis': {'title': "Density Estimation"},
                     'title': '<b>{}</b> locations in densities for {} and {}'.format(chosen_state, initial_year, final_year)
                     }
    
    Density = {
        'data': Density_Data,
        'layout': Density_Layout
    }
    return Density

 

############################################################   
    


@app.callback(
    Output('rank-path-graph', 'figure'),
    [Input('rankpath_dropdown','value'),
     Input('years-slider-rank-path','value')]
)
def update_rankpath(rank_selected, year_selected_slider): #year_hovered,
    
    df_map = us_tidy[us_tidy.Year == str(first_year)]
    
    #if year_hovered is None: 
    year = year_selected_slider
    
    #else:
    #    year = year_hovered['points'][0]['x']

    chosen_rank = int(rank_selected)
    
    rp_aux = us_tidy[us_tidy.Rank == chosen_rank].sort_values('Year')

    rp_aux['x'] = rp_aux.geometry.centroid.x
    rp_aux['y'] = rp_aux.geometry.centroid.y
    rp_aux['dot_color'] = np.where(np.isin(rp_aux.Year, str(year)), '#0066FF', 'red')
    rp_aux['dot_size'] = np.where(np.isin(rp_aux.Year, str(year)), 14, 0)

    state_highlighted = rp_aux[rp_aux.Year == str(year)].Name.values[0]
    
    RankPath_Layout = dict(
        projection = dict(type='albers usa'),
        title = '<b>RankPath for the Rank {} and highlighted {}: {}</b>'.format(chosen_rank, year, state_highlighted),
        titlefont = {"size": 24,
                     "family": "Courier New"},
        hovermode = 'closest',
        paper_bgcolor = 'rgb(233,233,255)', 
        plot_bgcolor = 'rgb(233,233,255)',
        xaxis = dict(
            autorange = True, # False,
            #range = [-125, -65],
            showgrid = False,
            zeroline = False,
            fixedrange = True
        ),
        yaxis = dict(
            autorange = True, #False,
            #range = [25, 49],
            showgrid = False,
            zeroline = False,
            fixedrange = True
        ),
        #margin = dict(
        #    t=20,
        #    b=20,
        #    r=20,
        #    l=20
        #),
        width = 1100,
        height = 650,
        dragmode = 'select'
    )
           
    
    # I had to modify this code a little bit, because of the Multipolygon of shapely
    # Also, I had to convert to lists the centroids and the exteriors of the Polygon
    # http://toblerity.org/shapely/shapely.geometry.html
    # Several States had multiple centroids... so I chose to take the value of the convex_hull
    
    
    # Return Boggest polygon of a multipolygon object in python
    def return_biggest(mp):
        areas = [i.area for i in list(mp)]
        biggest = mp[areas.index(max(areas))]
        return biggest
    
    RankPath_Data = []
    for index,row in df_map.iterrows():
        if df_map['geometry'][index].type == 'Polygon':
            x,y = row.geometry.exterior.xy
            x = x.tolist()
            y = y.tolist()
            c_x,c_y = row.geometry.centroid.xy
            c_x = c_x.tolist()
            c_y = c_y.tolist()
        elif df_map['geometry'][index].type == 'MultiPolygon':
            x = return_biggest(df_map['geometry'][index]).exterior.xy[0].tolist()
            y = return_biggest(df_map['geometry'][index]).exterior.xy[1].tolist()
            c_x = [return_biggest(df_map['geometry'][index]).centroid.xy[0][0]]
            c_y = [return_biggest(df_map['geometry'][index]).centroid.xy[1][0]]
        else: 
            print('stop')
        county_outline = dict(
                type = 'scatter',
                showlegend = False,
                legendgroup = "shapes",
                line = dict(color='black', width=1.5),
                x=x,
                y=y,
                marker = dict(size=0.01), # Because of the hull_convex, some unusual dots appeared. So this argument removes them.
                fill='toself',
                fillcolor = 'lightyellow',
                hoverinfo='none'
        )
        hover_point = dict(
                type = 'scatter',
                showlegend = False,
                legendgroup = "centroids",
                name = row.Name,
                marker = dict(size=4, color = 'black'),
                x = c_x, #df.centroid.x, #c_x
                y = c_y, #df.centroid.y, #c_y
                fill='toself',
                fillcolor = 'red',
                hoverinfo = 'none'
        )
        RankPath_Data.append(county_outline)
        RankPath_Data.append(hover_point)
    
    rankpath_lines = dict(
                    x = rp_aux['x'], 
                    y = rp_aux['y'],
                    mode = 'lines', 
                    name = 'Path',
                    opacity = 1, # opacity_index/30,
                    hoverinfo = 'none',
                    line = dict(color = 'red', width = 4),
                    showlegend = False)
    rankpath_markers = dict(
                        x = rp_aux['x'], 
                        y = rp_aux['y'],
                        mode = 'markers',
                        hoverinfo = 'text',
                        marker = dict(size = rp_aux['dot_size'],# 12,
                                      color = rp_aux['dot_color'],
                                      opacity = 1),
                        name = '',
                        text = rp_aux['Name'],
                        showlegend = False)
    
    RankPath_Data.append(rankpath_lines)
    RankPath_Data.append(rankpath_markers)
        
    
    RankPath = dict(data = RankPath_Data, layout = RankPath_Layout)
    return RankPath

############################################################
    
@app.callback(
    Output('markov-pooled-graph', 'figure'),
    [Input('markov-pooled-classes-dropdown','value'),
     Input('markov-pooled-spatial-dropdown','value')])
def update_markov_pooled_graph(markov_class_value, markov_spatial_value):
    
    smc_df_aux = us_tidy[['Name', 'Year', 'PCR']].pivot(index = 'Name', columns = 'Year', values = 'PCR')

    sm = giddy.markov.Spatial_Markov(smc_df_aux, W, fixed = True, k = markov_class_value, m = markov_spatial_value)     
    
    shorrock_1 = mobility.markov_mobility(sm.p, measure="P")
    shorrock_2 = mobility.markov_mobility(sm.p, measure="D")
    som_con    = mobility.markov_mobility(sm.p, measure = "L2")
    
    Heatmap_Data = [dict(
                        type = 'heatmap',
                        x = list(string.ascii_lowercase[0:markov_class_value]),
                        y = list(reversed(list(string.ascii_uppercase[0:markov_class_value]))),
                        z = list(reversed(sm.p.tolist())) # Reversed list
                        )]
    
    Heatmap_Layout = dict(title = '<b>Pooled Markov transition probability matrix</b> <br>Shorrock 1\'s: {}, Shorrock 2\'s: {}, Sommers and Conlisk\'s: {}</br>'.format(round(shorrock_1, 2), round(shorrock_2, 2), round(som_con, 2)),
                          titlefont = {"size": 24,
                                      "family": "Arial"})
    
    Heatmap_Pooled = dict(data = Heatmap_Data, layout = Heatmap_Layout)
    #print(Heatmap_Pooled)    
    return Heatmap_Pooled

############################################################ 
    





############################################################
    
@app.callback(
    Output('markov-spatial-graph', 'figure'),
    [Input('markov-pooled-classes-dropdown','value'),
     Input('markov-pooled-spatial-dropdown','value')])
def update_markov_spatial_graph(markov_class_value, markov_spatial_value):
    
    smc_df_aux = us_tidy[['Name', 'Year', 'PCR']].pivot(index = 'Name', columns = 'Year', values = 'PCR')

    sm = giddy.markov.Spatial_Markov(smc_df_aux, W, fixed = True, k = markov_class_value, m = markov_spatial_value)     
    
    rows_number = math.ceil(markov_spatial_value/3)
    
    fig = tools.make_subplots(rows = rows_number, 
                              cols = 3, 
                              subplot_titles = tuple(['Spatial Lag ' + str(i) for i in list(range(markov_spatial_value))]))
    
    for r in list(range(rows_number)):
        for c in list(range(3)):
            i = r * 3 + c
            if(i == 0):
                xaxis_aux = None
                yaxis_aux = None
            else:    
                xaxis_aux = 'x' + str(i)
                yaxis_aux = 'y' + str(i)
            Heatmap_Data_Spatial_aux = dict(
                type = 'heatmap',
                name = 'Spatial Lag ' + str(i),
                x = list(string.ascii_lowercase[0:markov_class_value]),
                y = list(reversed(list(string.ascii_uppercase[0:markov_class_value]))),
                z = list(reversed(sm.P[i])), # Reversed list
                xaxis = xaxis_aux,
                yaxis = yaxis_aux
                )
            fig.append_trace(Heatmap_Data_Spatial_aux, r+1, c+1)
    
    fig['layout'].update(title = '<b>Spatial Lags Subplots</b>', 
                         titlefont = {"size": 18,
                                      "family": "Arial"})
    #print(fig['data'])
    #print(fig)
    #print('row number: ', rows_number)
    Heatmap_Spatial = dict(data = fig['data'], layout = fig['layout'])   
    return Heatmap_Spatial

############################################################ 
    








############################################################   
    


@app.callback(
    Output('lima-neighborhood-graph', 'figure'),
    [Input('rank-range-slider','value')]
)
def update_lima_neighborhood(pair_years_range_slider):
    
    us_tidy_map = us_tidy[us_tidy.Year == str(first_year)]
    
    y_initial = us_tidy[us_tidy.Year == str(pair_years_range_slider[0])].PCR
    y_final   = us_tidy[us_tidy.Year == str(pair_years_range_slider[1])].PCR
    
    global_spatial_tau = giddy.rank.SpatialTau(np.array(y_initial), np.array(y_final), W, 999)
    
    tau_wr = giddy.rank.Tau_Local_Neighbor(y_initial, y_final, W, 999) 
    #tau_wr
    
    LIMA_Layout = dict(
        projection = dict(type='albers usa'),
        title = '<b>Neighbor set LIMA between {} and {} (Spatial Kendall\'s Tau: {})</b>'.format(str(pair_years_range_slider[0]),str(pair_years_range_slider[1]), str(round(global_spatial_tau.tau_spatial, 2))),
        titlefont = {"size": 24,
                     "family": "Courier New"},
        hovermode = 'closest',
        paper_bgcolor = 'rgb(233,233,255)', 
        plot_bgcolor = 'rgb(233,233,255)',
        xaxis = dict(
            autorange = True, # False,
            #range = [-125, -65],
            showgrid = False,
            zeroline = False,
            fixedrange = True
        ),
        yaxis = dict(
            autorange = True, #False,
            #range = [25, 49],
            showgrid = False,
            zeroline = False,
            fixedrange = True
        ),
        #margin = dict(
        #    t=20,
        #    b=20,
        #    r=20,
        #    l=20
        #),
        width = 1100,
        height = 650,
        dragmode = 'select'
    )
           
    
    # I had to modify this code a little bit, because of the Multipolygon of shapely
    # Also, I had to convert to lists the centroids and the exteriors of the Polygon
    # http://toblerity.org/shapely/shapely.geometry.html
    # Several States had multiple centroids... so I chose to take the value of the convex_hull
    
    
    # Return Boggest polygon of a multipolygon object in python
    def return_biggest(mp):
        areas = [i.area for i in list(mp)]
        biggest = mp[areas.index(max(areas))]
        return biggest
    
    cmap = matplotlib.cm.get_cmap('Reds') #matplotlib.cm.get_cmap('Spectral')
    
    LIMA_Data = []
    for index,row in us_tidy_map.iterrows():
        if us_tidy_map['geometry'][index].type == 'Polygon':
            x,y = row.geometry.exterior.xy
            x = x.tolist()
            y = y.tolist()
            c_x,c_y = row.geometry.centroid.xy
            c_x = c_x.tolist()
            c_y = c_y.tolist()
        elif us_tidy_map['geometry'][index].type == 'MultiPolygon':
            x = return_biggest(us_tidy_map['geometry'][index]).exterior.xy[0].tolist()
            y = return_biggest(us_tidy_map['geometry'][index]).exterior.xy[1].tolist()
            c_x = [return_biggest(us_tidy_map['geometry'][index]).centroid.xy[0][0]]
            c_y = [return_biggest(us_tidy_map['geometry'][index]).centroid.xy[1][0]]
        else: 
            print('stop')
        county_outline = dict(
                type = 'scatter',
                showlegend = False,
                legendgroup = "shapes",
                line = dict(color='black', width=1.5),
                x = x,
                y = y,
                marker = dict(size=0.01), # Because of the hull_convex, some unusual dots appeared. So this argument removes them.
                fill='toself',
                fillcolor = matplotlib.colors.rgb2hex(cmap(tau_wr.tau_ln[index])),
                colorscale = 'Viridis',
                hoverinfo = 'text',
                text = 'LIMA: ' + str(round(tau_wr.tau_ln[index], 3))
        )
        LIMA_Data.append(county_outline)       
    
    LIMA = dict(data = LIMA_Data, layout = LIMA_Layout)
    return LIMA

############################################################
    




############################################################   
    


@app.callback(
    Output('rose-graph', 'figure'),
    [Input('rose-range-slider','value'),
     Input('rose-k','value')]
)
def update_rose(rose_pair_years_range_slider, rose_k):
    
    y_initial = us_tidy[us_tidy.Year == str(rose_pair_years_range_slider[0])].PCR
    y_final   = us_tidy[us_tidy.Year == str(rose_pair_years_range_slider[1])].PCR
    
    Y = np.swapaxes(np.array([y_initial, y_final]), 0, 1)

    r4 = giddy.directional.Rose(Y, W, k = rose_k)
    r_aux = list(map(math.degrees, r4.theta.tolist()))
    
    Rose_Data = [dict(
        type = 'scatterpolargl',
        r = r4.r.tolist(),
        theta = r_aux,
        mode = 'markers',
        marker = dict(
            color = 'peru'
        )
        )]

    Rose_Layout = dict(
        title = '<b>Rose for {} and {} (k = {})</b>'.format(rose_pair_years_range_slider[0], rose_pair_years_range_slider[1], rose_k),
        showlegend = False
    )
    
    Rose_Fig = dict(data = Rose_Data, layout = Rose_Layout)
    return Rose_Fig

############################################################




if __name__ == '__main__':
    app.run_server()
