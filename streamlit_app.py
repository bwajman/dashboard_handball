import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# function
def format_number(number):
    if number >= 1000000:
        return f"{number / 1000000:.3f}m"
    elif number >= 1000:
        return f"{number / 1000:.3f}k"
    else:
        return str(number)

def count_result(df,x):
    return int(df['RESULT'].loc[df['RESULT']==x].count())

def score_result(df,x):
    return round(int(df[x].sum()),2)

# load dataframe
csv = 'data/handball.csv'
df = pd.read_csv(csv)

# sidebar
st.sidebar.title(':magic_wand: Provide your filter below:')

# select teams
teams = sorted(set(list(df['H_team'].unique())+list(df['A_team'].unique())))
teams = st.sidebar.multiselect('Select team which you want to find',teams,default=None)

selected = False
if len(teams)>0:
    selected = True

# select home or away matches
st.sidebar.caption('Home or Away matches:')
home = st.sidebar.checkbox('HOME',value=True,disabled=not selected)
away = st.sidebar.checkbox('AWAY',value=True,disabled=not selected)

if home and away:
    mask = ((df['H_team'].isin(teams))|(df['A_team'].isin(teams)))
elif home:
    mask = df['H_team'].isin(teams)
elif away:
    mask = df['A_team'].isin(teams)
else:
    selected  = False

# select result of matches
st.sidebar.caption('Result of matches:')
win = st.sidebar.checkbox('Home WIN',value=True,disabled=not selected)
draw = st.sidebar.checkbox('DRAW',value=True,disabled=not selected)
lost = st.sidebar.checkbox('Away WIN',value=True,disabled=not selected)

results = []
if win:
    results.append('H')
if draw:
    results.append('D')
if lost:
    results.append('A')

# select range of date
values_h = st.sidebar.slider('Select a score of home team',min_value =df['H_score'].min() , max_value =df['H_score'].max() ,value=(df['H_score'].min(), df['H_score'].max()), disabled=not selected)
values_a = st.sidebar.slider('Select a score of away team',min_value =df['A_score'].min() , max_value =df['A_score'].max() ,value=(df['A_score'].min(), df['A_score'].max()), disabled=not selected)

min_date = datetime.strptime(df['DATE'].min(), '%Y-%m-%d').date()
max_date = datetime.strptime(df['DATE'].max(), '%Y-%m-%d').date()

values_date = st.sidebar.slider('Select a range of date',value=(min_date, max_date), disabled=not selected)

# select type of match
type_match = st.sidebar.radio("Additional information about match:",["REGULAR TIME", "ET", "PEN","AWA.","ABN.","CAN.","WO."], disabled= not selected)
st.sidebar.caption('**INFORMATION**: \n ET - Extra Time • PEN - Penatly • AWA. - Awarded • ABN. - Abandoned • CAN. - Cancel • WO. - Walkover')

type  = []
if type_match == 'REGULAR TIME':
    info = df['INFO'].isnull()
else:
    type.append(type_match)
    info = df['INFO'].isin(type)

# create dataframe with all filter above
if selected and (home or away):
    df_masked = df.loc[mask
                   &
                   df['RESULT'].isin(results)
                   &
                   df['H_score'].between(values_h[0],values_h[1])
                   &
                   df['A_score'].between(values_a[0], values_a[1])
                   &
                   info
                   &
                   df['DATE'].between(str(values_date[0]),str(values_date[1]))
                   ]

# main page
st.header(':bar_chart: statistic of handball :comet: ', divider='red')

if not home and not away:
    st.error("Select at least one option from Home or Away matches if you want check team!")

# calculate variable for first section
count = df.shape[0]
seasons = len(df['SEASON'].unique())
countries = len(df['COUNTRY'].unique())
competitions = len(df['COMPETITION'].unique())
if selected == True:
    count_masked = df_masked.shape[0]
    seasons_masked = len(df_masked['SEASON'].unique())
    countries_masked = len(df_masked['COUNTRY'].unique())
    competitions_masked = len(df_masked['COMPETITION'].unique())
with st.expander("Basic information about selected teams:"):
    col1, col2, col3, col4 = st.columns(4)
    if not selected:
        col1.metric(":crossed_swords: matches", count,delta_color="inverse", help = 'numbers of selected matches')
        col2.metric(":date: seasons", seasons, help='numbers of selected seasons')
        col3.metric(":earth_africa: countries", countries, help='numbers of selected countries')
        col4.metric(":checkered_flag: competitions", competitions, help='numbers of selected competitions')
    elif selected== True:
        col1.metric(":crossed_swords: matches", count_masked,count,delta_color="off", help = 'numbers of selected matches')
        col2.metric(":date: seasons", seasons_masked, seasons,delta_color="off", help='numbers of selected seasons')
        col3.metric(":earth_africa: countries", countries_masked, countries, delta_color="off", help='numbers of selected countries')
        col4.metric(":checkered_flag: competitions", competitions_masked, competitions,  delta_color="off", help='numbers of selected competitions')

    col5, col6, col7, col8, col9 = st.columns(5)
    if not selected:
        col5.metric(":goal_net: home score:", format_number(score_result(df,'H_score')),  delta_color="off", help='goals scored by home team')
        col6.metric(":goal_net: away score", format_number(score_result(df,'A_score')),  delta_color="off", help='goals scored by away team')
        col7.metric(":house: home win", count_result(df,'H'),  delta_color="off", help='numbers of matches win by home team')
        col8.metric(":handshake: draw", count_result(df,'D'),  delta_color="off", help='numbers of draw matches')
        col9.metric(":airplane: away win", count_result(df,'A'),  delta_color="off", help='numbers of matches win by away team')
    elif selected == True:
        col5.metric(":goal_net: home score:", score_result(df_masked,'H_score'), score_result(df,'H_score'),  delta_color="off", help='goals scored by home team')
        col6.metric(":goal_net: away score", score_result(df_masked,'A_score'), score_result(df,'A_score'),  delta_color="off", help='goals scored by away team')
        col7.metric(":house: home win", count_result(df_masked,'H'),count_result(df,'H'),  delta_color="off", help='numbers of matches win by home team')
        col8.metric(":handshake: draw", count_result(df_masked,'D'),count_result(df,'D'),  delta_color="off", help='numbers of draw matches')
        col9.metric(":airplane: away win", count_result(df_masked,'A'),count_result(df,'A'),  delta_color="off", help='numbers of matches win by away team')


# view dataframe in case
st.subheader('Selected matches:')
if selected and (home or away):
    if selected:
        color = st.checkbox('Mark selected teams', value=False)
    if color:
        st.dataframe(df_masked.style.applymap(lambda x: 'background-color: yellow;' if x in teams and x in df_masked[['H_team','A_team']].values else '', subset=['H_team','A_team']),hide_index=True)
    else:
        st.dataframe(data=df_masked, width=5000, height=350, hide_index=True, use_container_width=True)
    chart_pie = df_masked['RESULT'].value_counts()
    chart_bar = df_masked[['H_score','A_score']].sum()
else:
    st.dataframe(data=df, width=5000, height=350, hide_index=True, use_container_width=True)
    chart_pie = df['RESULT'].value_counts()
    chart_bar = df[['H_score','A_score']].sum()

# prepare charts
pie_chart = px.pie(chart_pie,
                title='Result of matches from perspective home team',
                values=chart_pie.values,
                names=chart_pie.index)

bar_chart = px.bar(chart_bar,title='Goals scored',
                   x=chart_bar.index,
                   y=chart_bar.values, text_auto=True)

with st.expander("Show charts with stats:"):
    st.plotly_chart(pie_chart)
    st.plotly_chart(bar_chart)
