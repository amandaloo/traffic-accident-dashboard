#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#import libraries
import pandas as pd


# In[ ]:


#load data
accident = pd.read_csv("US_Accidents_subset.csv")


# In[ ]:


#data cleaning
#convert Start_Time to dateime
accident['Start_Time'] = pd.to_datetime(accident['Start_Time'], format='mixed')

#derive year and month
accident['Year'] = accident['Start_Time'].dt.year
accident['Month'] = accident['Start_Time'].dt.month
accident['Month_Name'] = accident['Start_Time'].dt.month_name()

#all accidents occur in US, 44% of end_lat and end_lng values are null, Timezone is dependent on state, Turning_Loop are all false
accident = accident.drop(columns=['Country','End_Lat','End_Lng','Timezone','Turning_Loop']) 
accident = accident.dropna(
    subset=['State','Severity','Start_Time','Start_Lat','Start_Lng']) #drop any NA values
accident = accident.sort_values(by=['State','Severity']) #sort by state and severity


# In[ ]:


# APP BUILDING
import streamlit as st
import plotly.express as px


# In[ ]:


#create page
st.title('US Traffic Accidents Dashboard')
st.write("""
This dashboard explores traffic accident patterns across the United States from 2016-2023. 
It provides interactive visualizations of accident locations, severity levels, weather conditions, and accident trends over time.
""")


# In[ ]:


#sidebar filters
#state filter
states = ['All'] + sorted(accident['State'].unique())
selected_state = st.sidebar.selectbox('Select State', states)

#severity filter
severity_options = sorted(accident["Severity"].unique())
selected_severity = st.sidebar.multiselect("Select Severity Level",severity_options,default=severity_options)

#time filter
min_date = accident["Start_Time"].min().date()
max_date = accident["Start_Time"].max().date()

selected_dates = st.sidebar.date_input("Select Time Period",value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

#apply filters
filtered = accident.copy()

if selected_state != "All":
    filtered = filtered[
        filtered["State"] == selected_state]

filtered = filtered[
    filtered["Severity"].isin(selected_severity)]

if len(selected_dates) == 2:
    start_date, end_date = selected_dates

    filtered = filtered[
        (filtered["Start_Time"].dt.date >= start_date) &
        (filtered["Start_Time"].dt.date <= end_date)]


# In[ ]:


#Accident Overview plot
st.subheader("Accident Overview")
st.caption("""
A summary of accident statistics based on the currently selected filters,
including total accidents, average severity, and geographic coverage.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Accidents",
        f"{len(filtered):,}"
    )

with col2:
    avg_severity = filtered["Severity"].mean()
    st.metric(
        "Average Severity",
        f"{avg_severity:.2f}" if pd.notna(avg_severity) else "N/A"
    )

with col3:
    states_affected = filtered["State"].nunique()
    st.metric(
        "States Represented",
        states_affected
    )

st.divider()


# In[ ]:


#Accident Density Map plot
st.subheader("Accident Locations")
st.caption("""
This density map highlights geographic areas with higher concentrations
of reported traffic accidents. Darker spots represent higher severity accidents.
""")

map_data = filtered.dropna(
    subset=["Start_Lat", "Start_Lng"]
)

# Limit plotted points for performance
MAX_MAP_POINTS = 100_000

if len(map_data) > MAX_MAP_POINTS:

    map_data = map_data.sample(
        n=MAX_MAP_POINTS,
        random_state=42)
st.caption(
    f"Displaying a sample of {len(map_data):,} "
    f"locations from {len(filtered):,} filtered accidents."
)

fig_map = px.density_map(
    map_data,
    lat="Start_Lat",
    lon="Start_Lng",
    color_continuous_scale="Blues",
    center={"lat": 39.5, "lon": -98.35}, #center around US
    hover_data=["State", "Severity"],
    zoom=3,
    radius=8,
    height=600,
    title="Geographic Distribution of Accidents"
)

st.plotly_chart(fig_map, use_container_width=True)

st.caption("""
From this map we see that accidents are heavily localized among densely populated cities, such as Minneapolis, Chicago, Philidelphia, and Salt Lake City.
""")

st.divider()


# In[ ]:


#Severity Distribution bar chart
st.subheader("Accident Severity Distribution")
st.caption("""
This chart displays the distribution of accidents across severity levels.
Severity ranges from Level 1 (least impact) to Level 4 (highest impact),
allowing users to compare the frequency of different accident severities.
""")

severity_counts = (
    filtered["Severity"]
    .value_counts()
    .sort_index()
    .reset_index()
)

severity_counts.columns = ["Severity", "Accidents"]

fig_severity = px.bar(
    severity_counts,
    x="Severity",
    y="Accidents",
    color="Severity",
    color_discrete_sequence=px.colors.sample_colorscale(
        "Blues",
        [0.25, 0.45, 0.70, 1.0]
    ),    
    text="Accidents",
    title="Number of Accidents by Severity",
    labels={
        "Severity": "Severity Level",
        "Accidents": "Number of Accidents"
    }
)

st.plotly_chart(
    fig_severity,
    use_container_width=True
)

st.caption("""
A severity Level 2 was the most common, with 6 million+ accidents. The lowest severity level was Level 1, with only 67,366 accidents.
""")

st.divider()


# In[ ]:


#Weather conditions plot
st.subheader("Accidents by Visability")
st.caption("""
The bar chart examines the association between reported visibility conditions and the number of recorded traffic accidents. 
Visibility measurements were grouped into intervals to make accident frequency easier to compare across different conditions.
""")

#define visibility intervals (miles)
visibility_bins = [0, 1, 2, 5, 10, 15, 20, float("inf")]

visibility_labels = [
    "0–1 miles",
    "1–2 miles",
    "2–5 miles",
    "5–10 miles",
    "10–15 miles",
    "15–20 miles",
    "20+ miles"
]

#define visibility colors
blue_shades = px.colors.sample_colorscale(
    "Blues",
    [0.95, 0.80, 0.65, 0.50, 0.35, 0.20, 0.05]
)

visibility_colors = dict(zip(visibility_labels, blue_shades))

weather_data = filtered.dropna(subset=["Visibility(mi)"]).copy()

weather_data["Visibility_Range"] = pd.cut(
    weather_data["Visibility(mi)"],
    bins=visibility_bins,
    labels=visibility_labels,
    include_lowest=True)

#calculate accident counts
visibility_counts = (
    weather_data["Visibility_Range"]
    .value_counts(sort=False)
    .reset_index())

visibility_counts.columns = ["Visibility Range", "Accident Count"]

#plot
fig_visibility = px.bar(
    visibility_counts,
    x="Visibility Range",
    y="Accident Count",
    color="Visibility Range",
    color_discrete_map=visibility_colors,
    text="Accident Count",
    category_orders={'Visibility Range': visibility_labels},
    title="Accident Counts Across Visibility Ranges",
    labels={
        "Visibility Range": "Visibility (Miles)",
        "Accident Count": "Number of Accidents"
    })

fig_visibility.update_traces(
    texttemplate="%{text:,.0f}",
    textposition="outside")

fig_visibility.update_layout(
    xaxis_title="Visibility Range (Miles)",
    yaxis_title="Number of Accidents",
    coloraxis_showscale=False)

st.plotly_chart(fig_visibility, use_container_width=True)

st.caption("""
A visibility range of 5-10 miles was the most common observed, with 6 million+ accidents.
Visibility ranges of 0-1 miles, 1-2 miles, and 2-5 miles were also relatively common, while visibility 10+ miles was not very common.
""")

st.divider()


# In[ ]:


#Accident Trend over time
st.subheader("Accident Trends Over Time")
st.caption("""
This line chart illustrates monthly accident frequency over the selected
time period. It helps identify temporal patterns, seasonal fluctuations,
and changes in accident frequency over time.
""")

#aggregate accidents by month
monthly_trends = (
    filtered
    .set_index("Start_Time")
    .resample("ME")
    .size()
    .reset_index(name="Accidents")
)

fig_trend = px.line(
    monthly_trends,
    x="Start_Time",
    y="Accidents",
    markers=True,
    title="Monthly Accident Trends",
    labels={
        "Start_Time": "Date",
        "Accidents": "Number of Accidents"
    }
)

st.plotly_chart(
    fig_trend,
    use_container_width=True
)

st.caption("""
From 2016 until September 2019, the number of recorded monthly accidents was under 100K.
There is a signficant dip in accidents in July and August 2020, which may have been due to Covid-19 and people were not leaving their house as often.
Then we see an overall increase in monthly accidents from 2021 to 2023.
""")


# In[ ]:


#Data preview
with st.expander("View Filtered Dataset"):
    st.dataframe(
        filtered.head(1000),
        use_container_width=True)

    st.caption(f"Showing up to 1,000 of {len(filtered):,} filtered records.")

