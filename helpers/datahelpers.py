import pandas as pd 
import requests 
from bs4 import BeautifulSoup

class Scrape:
    url : str 

    def __init__(self, url):
        self.url = url 
    
    def scrape_mlb_pitchers(self, num_pages=50) -> pd.DataFrame:
        """
        Manually scrapes off mlb.com for player data that I want. Defaults to 50 pages.
        Note: If IP and teams stop showing up, increase the number of pages.
        """
        all_player_ids = []
        all_player_names = []
        all_teams = []
        all_innings = []
        all_whip = []
        
        for page in range(1, num_pages + 1):
            page_url = self.url
            if page > 1:
                page_url += f'&page={page}'

            response = requests.get(page_url)

            soup = BeautifulSoup(response.text, 'html.parser')
            
            if soup.find('div', {'class': 'no-results-message-2ndKiuBC'}):
                break

            div_table = soup.find('div', {'class' : 'stats-body-table player'})

            player_ids = []
            player_names = []

            a_tags = div_table.find_all('a', {'class' : 'bui-link', 'tabindex' : '0'})
            teams = [td.get_text(strip=True) for td in div_table.find_all('td', {'data-col': '1'})]
            innings = [td.get_text(strip=True) for td in div_table.find_all('td', {'data-col': '11'})]
            whip = [td.get_text(strip=True) for td in div_table.find_all('td', {'data-col': '19'})]

            for a in a_tags:
                try:
                    player_id = a['href'].split('/')[-1]
                    name = a['aria-label']
                    if player_id.isdigit():
                        player_ids.append(player_id)
                        player_names.append(name)
                except:
                    pass
            
            all_player_ids.extend(player_ids)
            all_player_names.extend(player_names)
            all_teams.extend(teams)
            all_innings.extend(innings)
            all_whip.extend(whip)
        
        data = pd.DataFrame({'mlbID' : all_player_ids, 
                            'player_name' : all_player_names, 
                            'team' : all_teams, 
                            'IP' : all_innings, 
                            'whip' : all_whip})
        return data

    def load_qualifier(self) -> dict[str:float]:
        """
        Want the key value pairs of qualified teams for each player. Ideally, it should be
        something like "Cleveland" : 16.0. Qualified player will be 1 IP per game for respective team.
        """
        
        team_mapping = {'LA Dodgers': 'LAD', 'San Diego': 'SD', 'Houston': 'HOU','Arizona': 'AZ',
        'Pittsburgh': 'PIT', 'NY Yankees': 'NYY', 'Texas': 'TEX', 'Kansas City': 'KC', 'Tampa Bay': 'TB', 'Seattle': 'SEA',
        'St. Louis': 'STL', 'Boston': 'BOS', 'Oakland': 'OAK', 'Colorado': 'COL', 'Miami': 'MIA', 'Toronto': 'TOR',
        'SF Giants': 'SF', 'Philadelphia': 'PHI', 'Washington': 'WSH', 'NY Mets': 'NYM', 'Cleveland': 'CLE',
        'Cincinnati': 'CIN', 'LA Angels': 'LAA', 'Chi Sox': 'CWS', 'Chi Cubs': 'CHC', 'Baltimore': 'BAL',
        'Detroit': 'DET', 'Atlanta': 'ATL', 'Minnesota': 'MIN', 'Milwaukee': 'MIL'
        }

        df = pd.read_html(self.url)[0]
        teams_dict = {team_mapping.get(team, team): innings for team, innings in zip(df['Team'], df['2024'].astype(float))}

        return teams_dict 