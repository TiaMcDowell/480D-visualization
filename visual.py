import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
import calendar
df= pd.read_csv("ICBC_reported_crashes_Full_Data_data.csv")
flag_symbols = {
    'ANIMAL': 'A',
    'CYCLIST': 'C',
    'MOTORCYCLE': 'M',
    'PEDESTRIAN': 'P',
    'VEHICLE ONLY': 'V'
}

flag_colors = {
    'ANIMAL': 'goldenrod',
    'CYCLIST': 'red',
    'MOTORCYCLE': 'blue',
    'PEDESTRIAN': 'pink',
    'VEHICLE ONLY': 'gray'
}


flag_columns = list(flag_symbols.keys())[:-1]
flag_default = list(flag_symbols.keys())[-1]

def combine_flags(row):
    values = []
    for flag in flag_columns:
        if row[flag.capitalize() + ' Flag'] == 'Y':
            values.append(flag)
    
    if len(values) == 0:
        return flag_default
    else:
        return ', '.join(values)
 

def flags_to_symbols(row):
    flags = row['Flags']
    if flags in flag_symbols:
        return flag_symbols[flags]
    else:
        symbols = [flag_symbols[x] for x in flags.split(', ')]
        if len(symbols) == 0:
            return '_'
        else:
            return ''.join(sorted(symbols))

def flags_to_colors(row):
    flags = row['Flags']
    if flags in flag_colors:
        return flag_colors[flags]
    else:
        return 'gray'
# def size(row):
#     return 10


df['Flags'] = df.apply(combine_flags, axis=1)
df['Flag Symbols'] = df.apply(flags_to_symbols, axis=1)
df['Flag Colors'] = df.apply(flags_to_colors, axis=1)
# df['Node Size'] = df.apply(size, axis=1)

months = {month.upper(): index for index, month in enumerate(calendar.month_name) if month}

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1(children='Victoria Car Crashes by Street',
            style={
            'textAlign': 'center',
        }
    ),
    html.P(
        children='Symbols',
        style={
            'textAlign': 'center',
            'font-weight': "bold"
        }
    ),
    html.P(
        children='A=Animal M=Motercycle C=Cyclist P=Pedestrian V=Vehicle Only',
        style={
            'textAlign': 'center',
        }
    ),
    dcc.Graph(id="graph"),
    dcc.RangeSlider(
        id="range",
        marks={i: '{}:00-{}:99'.format(i*3, ((i+1)*3)-1) for i in range(0, 8)},
        min=0,
        max=7,
        value=[0, 7]
    ),
    html.Button("Go Forward", id='btn_forward', n_clicks=0, style={'margin': '2px'}),
    html.Button("Go Backwards", id='btn_backwards', n_clicks=0)
])

roadOffsets = {"JANUARY": {}, "FEBRUARY":{},"MARCH":{}, "APRIL":{}, "MAY":{}, "JUNE":{}, "JULY":{}, "AUGUST":{}, "SEPTEMBER":{}, "OCTOBER":{}, "NOVEMBER":{}, "DECEMBER":{}}

def getx(row):
    return row['table xy'][0]
def gety(row):
    return row['table xy'][1]

def chooseXY(row):
    if row["Street Full Name"] in roadOffsets[row['Month Of Year']]:
        roadOffsets[row['Month Of Year']][row["Street Full Name"]]["x"] += 1
        if roadOffsets[row['Month Of Year']][row["Street Full Name"]]["x"] % 35 == 0:
            roadOffsets[row['Month Of Year']][row["Street Full Name"]]["x"] = 0
            roadOffsets[row['Month Of Year']][row["Street Full Name"]]["y"] += 0.12
        return roadOffsets[row['Month Of Year']][row["Street Full Name"]]["x"], roadOffsets[row['Month Of Year']][row["Street Full Name"]]["y"]
    else:
        roadOffsets[row['Month Of Year']][row["Street Full Name"]] = {}
        roadOffsets[row['Month Of Year']][row["Street Full Name"]]["x"] = 0
        
        roadOffsets[row['Month Of Year']][row["Street Full Name"]]["y"] = months[row['Month Of Year']]
        
        return roadOffsets[row['Month Of Year']][row["Street Full Name"]]["x"], roadOffsets[row['Month Of Year']][row["Street Full Name"]]["y"]




df['table xy'] = df.apply (lambda row: chooseXY(row), axis=1)
df['table_x'] = df.apply (lambda row: getx(row), axis=1)
df['table_y'] = df.apply (lambda row: gety(row), axis=1)
    
@app.callback(
    Output("graph", "figure"), 
    [Input("btn_forward", "n_clicks"),
    Input("btn_backwards", "n_clicks"),
    Input("range", "value")]
    )
def display_graph(n_clicks1, n_clicks2, value):
    print(value)
    time_ranges = ['00:00-02:59','03:00-05:59','06:00-08:59', '09:00-11:59', '12:00-14:59', '15:00-17:59', '18:00-20:59', '21:00-23:59' ]
    searched_list = [time_ranges[i] for i in range(value[0], value[1]+1)]
    print(searched_list)
    
    n_clicks = n_clicks1 - n_clicks2

    RoadNames = []
    top5RoadNames = [0,0,0,0,0]
    for i in range(46519):
        if df["Street Full Name"][i] not in RoadNames:
            RoadNames.append(df["Street Full Name"][i])

    top5RoadNames[0] = RoadNames[n_clicks]
    top5RoadNames[1] = RoadNames[n_clicks + 1]
    top5RoadNames[2] = RoadNames[n_clicks + 2]
    top5RoadNames[3] = RoadNames[n_clicks + 3]
    top5RoadNames[4] = RoadNames[n_clicks + 4]
    
    only5mask = (
            (df["Street Full Name"] == top5RoadNames[0])
            | (df["Street Full Name"] == top5RoadNames[1])
            | (df["Street Full Name"] == top5RoadNames[2])
            | (df["Street Full Name"] == top5RoadNames[3])
            | (df["Street Full Name"] == top5RoadNames[4])
                ) & df['Time Category'].isin(searched_list)

    fig = px.scatter(df[only5mask],
                     x="table_x",
                     y="table_y",
                     opacity=0,
                     text='Flag Symbols',
                     color='Flag Symbols',
                     facet_col="Street Full Name",
                     height=750,
                     labels=dict(table_x="", table_y="Month"),
                     range_y=[0.8, 13],
                     color_discrete_sequence=["red", "gray", "green", "blue", "goldenrod", "magenta"],
                     hover_data={
                         'Crash Breakdown 2': False,
                         'Date Of Loss Year': False,
                         'Animal Flag': False,
                         'Crash Severity': True,
                         'Cyclist Flag': False,
                         'Day Of Week': True,
                         'Derived Crash Congifuration': False,
                         'Intersection Crash': False,
                         'Month Of Year': False,
                         'Motorcycle Flag': False,
                         'Municipality Name (ifnull)': False,
                         'Parking Lot Flag': False,
                         'Pedestrian Flag': False,
                         'Region': False,
                         'Street Full Name (ifnull)': False,
                         'Time Category': False,
                         'Municipality Name': False,
                         'Road Location Description': True,
                         'Street Full Name': False,
                         'Total Crashes': False,
                         'Flags': True,
                         'Flag Symbols': False,
                         'table xy': False,
                         'table_x': False,
                         'table_y': False,
                         'Flag Colors': False
                     }
                    )
    fig.update_xaxes(showticklabels=False)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
    fig.for_each_trace(lambda t: t.update(textfont_size=9,textfont_color=t.marker.color, showlegend=False))

    fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
    return fig
app.run_server(debug=False, use_reloader=False)