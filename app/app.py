import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk
from datetime import date

# SETTING PAGE CONFIG TO WIDE MODE
st.set_page_config(
        layout="wide",
        page_title="Emerging Areas"
        )

# LOADING DATA
DATE_TIME = "observation_start_date"
DATA_URL = (
    "app/sample_data/ea_sample.csv"
)

@st.cache(allow_output_mutation=True)
def load_data():
    data = pd.read_csv(DATA_URL)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    data[DATE_TIME] = pd.to_datetime(data[DATE_TIME])
    return data

data = load_data()
data['income_diff'] = data['income_inflow'] * data['inflow'] - data['income_outflow'] * data['outflow']
data_accumulated = data.copy()
data = data[[DATE_TIME, 'lat', 'lon','income_diff', 'total_net_flow', 'area_id']]

# Hackish way to color columns
def add_colors(data):
    data["color_r"] = 255/max(data['income_diff'])*data['income_diff']
    data["color_g"] = 10/max(data['income_diff'])*data['income_diff']
    data["color_b"] = 110/max(data['income_diff'])*data['income_diff']
    return data

def map(data, lat, lon, zoom):
    st.write(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state={
            "latitude": lat,
            "longitude": lon,
            "zoom": zoom,
            "pitch": 50,
        },
        layers=[
            pdk.Layer(
                plotting_option,
                data=data,
                get_position=["lon", "lat"],
                radius=1000,
                elevation_scale=0.0003,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
                get_elevation=['income_diff'],
                get_fill_color=['color_r', 'color_g', 'color_b']
            )
        ]
    ))

# LAYING OUT THE TOP SECTION OF THE APP
row1_1, row1_2 = st.beta_columns((2,3))

with row1_1:
    st.title("# Unacast - Emerging Areas - Miami Area 2019")
    month_selected = st.slider("Choose month", 1, 11,4)
    
my_expander = st.beta_expander("Adjust settings", expanded=False)

with my_expander:
    show_negative = False
    st.write("Filter for positive income influx areas or negative influx areas")
    agree = st.checkbox("Show negative outflow areas")
    if agree:
        show_negative = True


    plotting_option = st.selectbox('Plotting options',('ColumnLayer','HeatmapLayer'))

with row1_2:
    st.write(
    """
    ##
    Demo app showcasing the Emerging Areas dataset from Unacast. This simple app shows \
    areas whre the influx of people come from areas where the median income is higher, indicating that this in an "Emerging Area"
    """)

# FILTERING DATA BY HOUR SELECTED
data = data[data[DATE_TIME].dt.date <= date(2019,month_selected,1)]
data = data[['lat', 'lon', 'area_id', 'income_diff']].groupby('area_id').agg({'lat': 'first',
                                                                              'lon': 'first',
                                                                              'income_diff': 'sum'})

# LAYING OUT THE MIDDLE SECTION OF THE APP WITH THE MAPS
row2_1, row2_2, row2_3 = st.beta_columns((2,1,1))

miami = [25.7823907, -80.2994983]
zoom_level = 9


with row2_1:
    st.write("**Miami city from {} to {}".format(date(2019,month_selected, 1), date(2019,month_selected + 1, 1)))
    
    if show_negative:
        data_map = data.copy()
        data_map['income_diff'] = data_map['income_diff'] * (-1)
        data_map = data_map[data_map['income_diff'] > 0]
        data_map = add_colors(data_map)
        map(data_map, miami[0],miami[1], zoom_level)
    else:
        data_map = data.copy()
        data_map = data_map[data_map['income_diff'] > 0]
        data_map = add_colors(data_map)
        map(data_map, miami[0],miami[1], zoom_level)


# FILTERING DATA FOR THE CHART
filtered = data_accumulated[
    (data_accumulated[DATE_TIME].dt.date <= date(2019,month_selected+1,1))
    ]

sub_selection = filtered[['area_id', 'income_diff', 'inflow', 'outflow', 'total_net_flow']]
sub_selection = sub_selection.groupby(by=['area_id']).sum().sort_values(by=['income_diff'],ascending=False)
sub_selection['income_diff'] = sub_selection['income_diff'].astype('int32')

with row2_2:
    st.write("Top 10 performing tract areas accumulated over the period")
    st.write(sub_selection[['income_diff','total_net_flow']].head(10))

with row2_3:
    st.write("Bottom 10 performing tract areas accumulated over the period")
    st.write(sub_selection[['income_diff','total_net_flow']].tail(10))

row3_1, row3_2 = st.beta_columns((1,1)) 

with row3_1:
    st.write("Inflow and outflow of people in observed area")
    sub_selection_inflow = filtered[[DATE_TIME, 'inflow', 'outflow']]
    sub_selection_inflow= sub_selection_inflow.groupby(by=[DATE_TIME]).sum().sort_values(by=[DATE_TIME],ascending=False)
    chart_data = pd.DataFrame(sub_selection_inflow, columns=['inflow', 'outflow'])
    st.line_chart(chart_data, height=320)

with row3_2:
    st.write("Accumulated net flow of people in observed area")
    sub_selection_inflow = filtered[[DATE_TIME,'total_net_flow']]
    sub_selection_inflow= sub_selection_inflow.groupby(by=[DATE_TIME]).sum().sort_values(by=[DATE_TIME],ascending=False)
    sub_selection_inflow= sub_selection_inflow.loc[::-1, 'total_net_flow'].cumsum()[::-1]
    chart_data = pd.DataFrame(sub_selection_inflow, columns=['total_net_flow'])
    st.line_chart(chart_data, height=320)

st.slider