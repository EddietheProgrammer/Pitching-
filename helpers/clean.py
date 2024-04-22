import pickle
import pandas as pd
import os
import numpy as np
import scipy.stats as stats
from unidecode import unidecode

class Clean:
    models : dict 
    cols_wanted : list

    def __init__(self, models):
        self.models = models
        self.cols_wanted = ['release_speed', 'pfx_x', 'pfx_z', 'release_pos_x', 'release_pos_z', 'release_spin_rate', 
               'release_extension', 'velo_diff', 'px_diff', 'pz_diff',
                'zone', 'balls', 'strikes', 'plate_x', 'plate_z', 
                'batter_stance']

    @staticmethod
    def __load_model(pitch_name:str, model_dir='./pkl') -> any:
        """
        pitch_type str: the kind of pitch model to load. Can be FF-fastball, BB-breaking, or OF-offspeed.
        
        return: loaded model or None if file path is not found.
        """
        file = {
            'FF' : 'fastball.pkl',
            'BB' : 'breaking.pkl',
            'OF' : 'offspeed.pkl'
        }

        path = os.path.join(model_dir, file[pitch_name])
            
        if not os.path.exists(path):
            print(f'File not found for {pitch_name}. Does not exist')
            return None 

        return pickle.load(open(path, 'rb'))
    
    def __clean_training(self, df_sav:pd.DataFrame, fastball:list) -> pd.DataFrame:
        """
        Adds in features for baseball savant that are useful for my Breaking and Offspeed models.

        df: Dataframe. Ideally a savant dataset
        fastball: list of my fastball values to look for
        """
        df_sav = df_sav[df_sav['game_type'] == 'R']

        wanted = ['swinging_strike', 'swinging_strike_blocked']
        df_sav['whiff'] = df_sav['description'].isin(wanted).astype(int)

        # Change lefty trajectory to a righty for less to test
        df_sav['pfx_x'] = np.where(df_sav['p_throws'] == 'L', df_sav['pfx_x'].mul(-1), df_sav['pfx_x'])
        df_sav['release_pos_x'] = np.where(df_sav[f'p_throws'] == 'L', df_sav['release_pos_x'].mul(-1), df_sav['release_pos_x'])

        df_sav['plate_x'] = np.where(df_sav['p_throws'] == 'L', df_sav['plate_x'].mul(-1), df_sav['plate_x'])
        df_sav['batter_stance'] = df_sav['stand'].map({'L' : 0, 'R' : 1})

        mean_speed = df_sav[df_sav['pitch_name'].isin(fastball)].groupby('pitcher')['release_speed'].mean()
        df_sav['mean_speed'] = df_sav['pitcher'].map(mean_speed)
        df_sav['velo_diff'] = df_sav['mean_speed'] - df_sav['release_speed']

        mean_vert_break = df_sav[df_sav['pitch_name'].isin(fastball)].groupby('pitcher')['pfx_x'].mean()
        df_sav['mean_vert_break'] = df_sav['pitcher'].map(mean_vert_break)
        df_sav['px_diff'] = df_sav['mean_vert_break'] - df_sav['pfx_x']

        mean_hor_break = df_sav[df_sav['pitch_name'].isin(fastball)].groupby('pitcher')['pfx_z'].mean()
        df_sav['mean_hor_break'] = df_sav['pitcher'].map(mean_hor_break)
        df_sav['pz_diff'] = df_sav['mean_hor_break'] - df_sav['pfx_z']
        return df_sav

    def __add_pitching_plus(self, df_sav:pd.DataFrame) -> pd.DataFrame:
        """
        Ex: model = {
        ("Fastball", "Sinker") : fastball model
        ("Changeup", "Split-Finger") : offspeed model
        }
        """
        df = pd.DataFrame()

        for pitch_name, model in self.models.items():
            sub_df = df_sav[df_sav['pitch_name'].isin(pitch_name)]
            if 'Sinker' in pitch_name:
                cols_to_remove = ['velo_diff', 'px_diff', 'pz_diff']
                X_test = sub_df[[col for col in self.cols_wanted if col not in cols_to_remove]]
            else:
                X_test = sub_df[self.cols_wanted]
            
            prob = model.predict_proba(X_test)[:, 1]

            sub_df['prob'] = prob
            z_scores = (stats.zscore(sub_df['prob']) * 15) + 100
            sub_df['Pitching+'] = z_scores
            df = pd.concat([df, sub_df])

        return df.reset_index(drop=True)     

    @classmethod
    def streamlit_df(cls, df_sav:pd.DataFrame, df_fan:pd.DataFrame) -> pd.DataFrame:
        """
        df_sav: the savant dataset
        df_fan: the mlb.com dataset
        return: My new and IMPROVED savant dataset. Should be like fangraphs leaderboards for visualization sake.
        """
        fastball = ('4-Seam Fastball', 'Sinker')
        breaking = ('Slurve', 'Curveball', 'Knuckle Curve', 'Sweeper', 'Slider', 'Cutter')
        offspeed = ('Changeup', 'Split-Finger')

        fa = cls.__load_model(pitch_name='FF')
        br = cls.__load_model(pitch_name='BB')
        of = cls.__load_model(pitch_name='OF')
        models_dict = {fastball : fa, breaking : br, offspeed : of}

        clean = cls(models=models_dict)

        df_sav = clean.__clean_training(df_sav, fastball)

        remove = ['Other', 'Slow Curve', 'Eephus', 'Knuckleball', 'Pitch Out', 'Screwball', 'Forkball']
        df_sav = df_sav[~df_sav['pitch_name'].isin(remove)]


        df_sav = clean.__add_pitching_plus(df_sav)

        savant = df_sav # a helper variable for future when I want to map the Pitching+ values back to df

        df_sav = df_sav.groupby(['pitcher', 'pitch_name']).agg({'player_name' : 'first', 'Pitching+' : 'mean'}).reset_index()
        df_sav['Pitching+'] = round(df_sav['Pitching+'], 0).astype(int)

        df_sav = df_sav.pivot(index=['pitcher', 'player_name'], columns='pitch_name', values='Pitching+').reset_index()
        df_sav['Pitching+'] = round(df_sav['pitcher'].map(savant.groupby('pitcher')['Pitching+'].mean()), 0)
        df_sav['pitcher'] = df_sav['pitcher'].astype(str)
        df_sav = df_sav.join(df_fan.set_index('mlbID')[['IP', 'whip', 'team']], on='pitcher', how='left')
        df_sav['player_name'] = df_sav['player_name'].apply(lambda x: x.split(',')[1].strip() + ' ' + x.split(',')[0].strip())
        df_sav['player_name'] = df_sav['player_name'].apply(unidecode)
        df_sav['IP'] = df_sav['IP'].astype(float)
        # Reformatting the columns for the data frame
        df_sav = df_sav[['pitcher', 'player_name', 'team', 'IP', 'whip'] + [col for col in df_sav.columns if col not in ['pitcher', 'player_name', 'IP', 'team', 'whip']]]

        return df_sav
