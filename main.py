import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, JsCode
import pybaseball
from datetime import date
from helpers.clean import Clean
from helpers.datahelpers import Scrape
from fuzzywuzzy import fuzz
import warnings

st.set_page_config(page_title="Pitching Plus Leaders 2024", layout="wide")

warnings.filterwarnings("ignore")

today = str(date.today())

@st.cache_data
def load_savant(date):
    return pybaseball.statcast('2024-03-01', date)

@st.cache_data
def load_data_helpers(option:int) -> any:
    """
    Option must be 1 or 2!!!!! 
    1: Scrape mlb.com pitchers with their stats
    \n  2. Scrape Team Rankings for their innings qualifier
    """
    assert option in [1, 2]
    if option == 1:
        url = 'https://www.mlb.com/stats/pitching?playerPool=ALL&sortState=asc'
        helper = Scrape(url)
        return helper.scrape_mlb_pitchers()
    if option == 2:
        url = 'https://www.teamrankings.com/mlb/stat/games-played'
        helper = Scrape(url)
        return helper.load_qualifier()
    return 'Invalid option: Must be 1 or 2'

savant = load_savant(today)
pitching = load_data_helpers(1)

savant = Clean.streamlit_df(savant, pitching)

savant = savant.drop('pitcher', axis=1).sort_values(by="Pitching+", ascending=False)

st.markdown("""
<div class="header">
    <img src="https://github.com/EddietheProgrammer/Pitching-Plus/blob/Main/helpers/images/logo.png?raw=true" alt="logo" width="200" height="200" style="float: right; margin-left: 10px;"/>
    <img src="https://github.com/EddietheProgrammer/Pitching-Plus/blob/Main/helpers/images/logo.png?raw=true" alt="logo2" width="200" height="200" style="float: left; margin-right: 10px;"/>
    <div style="text-align: center;">
        <h1 style="color: white; font-weight: bold;">Pitching Plus Leaders 2024 🔥</h1>
    </div>
</div>
""", unsafe_allow_html=True)


labels = ["Qualified", 0, 1, 5, 10, 30, 60, 90, 150, 200, 250, 300]


category = st.selectbox("Min Playing Time (IP)", labels, index=0)

if category != 'Qualified':
    min_ip = float(category)
    savant = savant[savant['IP'] >= min_ip]
else:
    qualified = load_data_helpers(2)
    # I compiled a filter tool that filters the team in the savant team column then compares
    # if the inning is greater than or equal to the qualified values with respect to team. 
    savant['qualified'] = [True if team in qualified and innings >= qualified[team] else False for team, innings in zip(savant['team'], savant['IP'])]
    savant = savant[savant['qualified'] == True].drop('qualified', axis=1)

def get_similar_player_names(input_text):
    return [name for name in savant["player_name"] if fuzz.partial_ratio(name.lower(), input_text.lower()) >= 80]

text_search = st.text_input("Find a player", value="", autocomplete="on")

similar_player_names = get_similar_player_names(text_search)

if text_search and similar_player_names:
    savant = savant[savant["player_name"].isin(similar_player_names)]

jscode = JsCode("""
function(params) {
    var value = params.value;
   if (80 <= value && value < 100) {
        // Purple
        var ratio = (value - 80) / (100 - 80);
        color = 'rgb(' + Math.round(100 * ratio) + ', 72, 98)';
    }
    if (100 <= value && value <= 120) {
        // Green
        var ratio = (value - 100) / (120 - 100);
        color = 'rgb(0, ' + Math.round(220 * (1 - ratio)) + ', 20)';
    }
    
    return {
        'color': 'white',
        'backgroundColor': color 
    };
};
""")

gb = GridOptionsBuilder.from_dataframe(savant)
gb.configure_default_column(cellStyle={'color': 'black', 'font-size': '12px'},
                            suppressMenu=True, wrapHeaderText=True, autoHeaderHeight=True)

gb.configure_column("player_name", header_name="Player Name", width = 260)
gb.configure_column("team", header_name="Team")
gb.configure_column("whip", header_name="WHIP", width = 140)
gb.configure_column("IP", cellStyle={"textAlign": "left"}, headerClass="ag-left-aligned-header", width = 140)
gb.configure_column("Pitching+", cellStyle=jscode)
gb.configure_pagination(enabled=True)
go = gb.build()


custom_css = {
   ".ag-header-cell[col-id='IP']": {"text-align": "left"},
    ".ag-row-hover": {"background-color": "#808080 !important"},
    ".ag-row": {"background-color": "#E5E5E5"},
   ".ag-header-cell-text": {"color": "#D50032 !important;"},
}

AgGrid(savant, gridOptions=go, height=548, fit_columns_on_grid_load=True, custom_css=custom_css, columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        allow_unsafe_jscode=True)

st.markdown('<div style="text-align: right;"><em>Key: Darker Green=Good</em></div>', unsafe_allow_html=True)

st.write("\nAll Data comes from **Baseball Savant** and **MLB.com**")

st.markdown("""
Feel free to reach out to me on Twitter if you have any feedback: <a href="https://twitter.com/da_mountain_dew" style="color: white;">@da_mountain_dew</a>
""", unsafe_allow_html=True)

st.markdown("""
<span style='color:white'>
    <ul>
        <li> A qualified pitcher is one who has thrown at least 1 IP for every game a team has played.
        So if Justin Verlander throws 21 innings and his team has played 20 games, he would be considered a qualified pitcher. </li>
    </ul>
</span>
""", unsafe_allow_html=True)

st.markdown("""
<span style='color:white'>
    <ul>
        <li> Note: Pitching+ is a metric that objectively quantifies how well a pitch thrown
        can generate a whiff. I have an article that goes in depth on the statistic posted on
        my twitter and GitHub repository. Thanks. </li>
    </ul>
</span>
""", unsafe_allow_html=True)