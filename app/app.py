import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk
from datetime import date
# SETTING PAGE CONFIG TO WIDE MODE
st.set_page_config(layout="wide")

# LOADING DATA
DATE_TIME = "observation_start_date"
DATA_URL = (
    "app/sample_data/ea_sample.csv"
)

#@st.cache(persist=True)
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    data[DATE_TIME] = pd.to_datetime(data[DATE_TIME])
    return data

data = load_data(9600)
data_accumulated = data.copy()
data = data[[DATE_TIME, 'lat', 'lon','income_diff', 'total_net_flow', 'area_id']]

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
                "ColumnLayer",
                data=data,
                get_position=["lon", "lat"],
                radius=1000,
                elevation_scale=0.1,
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
    st.title("Unacast - Emerging Areas - Miami Area 2019")
    month_selected = st.slider("Choose month", 1, 11,5)
    

with row1_2:
    st.write(
    """
    ##
    Demo app showcasing the Emerging Areas dataset from Unacast. This simple app shows \
    areas whre the influx of people come from areas where the median income is higher, indicating that this in an "Emerging Area"
    """)
    show_negative = False
    st.write("Filter for positive income influx areas or negative influx areas")
    agree = st.checkbox("Show negative influx areas")
    if agree:
        show_negative = True


# FILTERING DATA BY HOUR SELECTED
data = data[data[DATE_TIME].dt.date == date(2019,month_selected,1)]


# LAYING OUT THE MIDDLE SECTION OF THE APP WITH THE MAPS
row2_1, row2_2, row2_3 = st.beta_columns((5,2,2))

miami = [25.7823907, -80.2994983]
zoom_level = 9


with row2_1:
    st.write("**Miami city from {} to {}".format(date(2019,month_selected,1), date(2019,month_selected+1,1)))
    
    if show_negative:
        data_map = data.copy()
        data_map['income_diff'] = data_map['income_diff'] *(-1)
        data_map = data_map[data_map['income_diff']>0]
        data_map = add_colors(data_map)
        map(data_map, miami[0],miami[1], zoom_level)
    else:
        data_map = data.copy()
        data_map = data_map[data_map['income_diff']>0]
        data_map = add_colors(data_map)
        map(data_map, miami[0],miami[1], zoom_level)

# FILTERING DATA FOR THE HISTOGRAM
filtered = data_accumulated[
    (data_accumulated[DATE_TIME].dt.date < date(2019,month_selected+1,1))
    ]
sub_selection = filtered[['area_id', 'income_diff', 'total_net_flow']]
sub_selection_v2 = sub_selection.groupby(by=['area_id']).sum().sort_values(by=['income_diff'],ascending=False)
sub_selection_v2['income_diff'] = sub_selection_v2['income_diff'].astype('int32')

with row2_2:
    st.write("Top 10 performing tract areas accumulated over the period")
    st.write(sub_selection_v2.head(10))

with row2_3:
    st.write("Bottom 10 performing tract areas accumulated over the period")
    st.write(sub_selection_v2.tail(10))

row3_1, _ = st.beta_columns((99,1))

with row3_1:
    st.write("Influx of people in observed area")
    sub_selection_inflow = filtered[['observation_start_date','total_net_flow']]
    sub_selection_inflow= sub_selection_inflow.groupby(by=[DATE_TIME]).sum().sort_values(by=['observation_start_date'],ascending=False)
    sub_selection_inflow = sub_selection_inflow.cumsum()
    chart_data = pd.DataFrame(sub_selection_inflow, columns=['total_net_flow'])
    st.area_chart(chart_data, height=320)

