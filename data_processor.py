import pandas as pd

def create_manager_history():
    # Read the games CSV
    games_df = pd.read_csv('data/raw/games.csv')
    
    # Filter for Premier League games (GB1) and seasons 2014-2024
    pl_games = games_df[
        (games_df['competition_id'] == 'GB1') & 
        (games_df['season'].between(2014, 2024))
    ]
    
    # Create separate dataframes for home and away games
    home_games = pl_games[['home_club_id', 'home_club_manager_name']].rename(
        columns={'home_club_id': 'club_id', 'home_club_manager_name': 'manager_name'}
    )
    
    away_games = pl_games[['away_club_id', 'away_club_manager_name']].rename(
        columns={'away_club_id': 'club_id', 'away_club_manager_name': 'manager_name'}
    )
    
    # Combine home and away games
    all_games = pd.concat([home_games, away_games])
    
    # Get unique combinations of club_id and manager with total counts
    manager_history = all_games.groupby(
        ['club_id', 'manager_name']
    ).size().reset_index(name='games_managed')
    
    # Sort by club_id to make it easier to read
    manager_history = manager_history.sort_values('club_id')
    
    # Save to new CSV file
    manager_history.to_csv('data/trans/manager_history.csv', index=False)
    
    return manager_history

def clean_manager_history():
    # Read the manager history CSV and pl_clubs CSV
    manager_df = pd.read_csv('data/trans/manager_history.csv')
    pl_clubs_df = pd.read_csv('data/trans/pl_clubs.csv')
    
    # Rename columns
    manager_df = manager_df.rename(columns={
        'home_club_id': 'club_id',
        'home_club_manager_name': 'manager_name'
    })
    
    # List of club_ids to remove
    clubs_to_remove = [
        603, 3008, 1010, 1031, 1071, 1110, 2288,
        641, 1032, 1039, 1123, 1132, 289, 512, 350, 399, 984
    ]
    
    # Filter out unwanted clubs and managers with less than 5 games
    manager_df = manager_df[
        (~manager_df['club_id'].isin(clubs_to_remove)) & 
        (manager_df['games_managed'] >= 10)
    ]
    
    # Merge with pl_clubs to get club names
    manager_df = manager_df.merge(
        pl_clubs_df[['club_id', 'name']],
        on='club_id',
        how='left'
    )
    
    # Save the cleaned data back to CSV
    manager_df.to_csv('data/trans/manager_history.csv', index=False)
    
    return manager_df

def clean_pl_clubs():
    # Read the pl_clubs CSV
    pl_clubs = pd.read_csv('data/trans/pl_clubs.csv')
    
    # Clean up club names by removing specified phrases
    pl_clubs['name'] = pl_clubs['name'].str.replace(' Football Club', '', case=False)
    pl_clubs['name'] = pl_clubs['name'].str.replace(' Association Football Club', '', case=False)
    
    # Save back to CSV
    pl_clubs.to_csv('data/trans/pl_clubs.csv', index=False)
    
    return pl_clubs

def fetch_manager_dates():
    # Read the necessary CSV files
    manager_df = pd.read_csv('data/trans/manager_history.csv')
    games_df = pd.read_csv('data/raw/games.csv')
    
    # Initialize lists to store dates
    start_dates = []
    end_dates = []
    
    # For each manager-club combination
    for _, row in manager_df.iterrows():
        # Find matches where manager appears for this club (home or away)
        club_matches = games_df[
            (
                ((games_df['home_club_id'] == row['club_id']) & 
                 (games_df['home_club_manager_name'] == row['manager_name'])) |
                ((games_df['away_club_id'] == row['club_id']) & 
                 (games_df['away_club_manager_name'] == row['manager_name']))
            )
        ]
        
        # Get the earliest and latest dates
        start_date = club_matches['date'].min()
        end_date = club_matches['date'].max()
        
        start_dates.append(start_date)
        end_dates.append(end_date)
    
    # Add the dates to the dataframe
    manager_df['start_date'] = start_dates
    manager_df['end_date'] = end_dates
    
    # Save updated dataframe back to CSV
    manager_df.to_csv('data/trans/manager_history.csv', index=False)
    
    return manager_df

def create_player_index():
    # Read necessary CSV files
    manager_df = pd.read_csv('data/trans/manager_history.csv')
    lineups_df = pd.read_csv('data/raw/game_lineups.csv')
    
    # Get unique club_ids from manager_history
    club_ids = manager_df['club_id'].unique()
    
    # Initialize empty dataframe for player index
    player_records = []
    
    # For each club
    for club_id in club_ids:
        # Filter lineups for this club
        club_lineups = lineups_df[lineups_df['club_id'] == club_id]
        
        # Get unique player combinations with their dates
        club_players = (
            club_lineups
            .groupby(['player_id', 'player_name', 'club_id'])
            .agg({
                'date': ['min', 'max']  # Get earliest and latest dates
            })
            .reset_index()
        )
        
        # Flatten column names
        club_players.columns = ['player_id', 'player_name', 'club_id', 'start_date', 'end_date']
        
        player_records.append(club_players)
    
    # Combine all player records
    player_index = pd.concat(player_records, ignore_index=True)
    
    # Sort by club_id and player_name
    player_index = player_index.sort_values(['club_id', 'player_name'])
    
    # Save to CSV
    player_index.to_csv('data/trans/player_index.csv', index=False)
    
    return player_index

def create_player_manager_relationships():
    # Read the CSVs
    player_df = pd.read_csv('data/trans/player_index.csv')
    manager_df = pd.read_csv('data/trans/manager_history.csv')
    
    # Create a mapping of unique manager names to IDs
    unique_managers = manager_df['manager_name'].unique()
    manager_id_mapping = {name: idx + 1 for idx, name in enumerate(sorted(unique_managers))}
    
    # Add manager_id to manager_df using the mapping
    manager_df['manager_id'] = manager_df['manager_name'].map(manager_id_mapping)
    
    # Save the updated manager_df back to CSV
    manager_df.to_csv('data/trans/manager_history.csv', index=False)
    
    # Convert dates to datetime for comparison
    for df in [player_df, manager_df]:
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])
    
    # Initialize list for new records
    new_records = []
    
    # For each player
    for _, player in player_df.iterrows():
        # Find all managers at the same club during player's tenure
        matching_managers = manager_df[
            (manager_df['club_id'] == player['club_id']) &
            (
                # Manager's tenure overlaps with player's tenure
                (
                    (manager_df['start_date'] <= player['end_date']) &
                    (manager_df['end_date'] >= player['start_date'])
                )
            )
        ]
        
        # Create a new record for each overlapping manager
        for _, manager in matching_managers.iterrows():
            new_record = player.copy()
            new_record['manager_id'] = manager['manager_id']
            new_record['manager_name'] = manager['manager_name']
            # Calculate overlapping period
            new_record['start_date'] = max(player['start_date'], manager['start_date'])
            new_record['end_date'] = min(player['end_date'], manager['end_date'])
            new_records.append(new_record)
    
    # Create new dataframe with all records
    player_manager_df = pd.DataFrame(new_records)
    
    # Sort by club_id, player_name, and start_date
    player_manager_df = player_manager_df.sort_values(['club_id', 'player_name', 'start_date'])
    
    # Save to CSV
    player_manager_df.to_csv('data/trans/player_index.csv', index=False)
    
    return player_manager_df

def add_player_valuations():
    # Read the CSVs
    player_index = pd.read_csv('data/trans/player_index.csv')
    valuations = pd.read_csv('data/raw/player_valuations.csv')
    
    # Convert dates to datetime
    player_index['start_date'] = pd.to_datetime(player_index['start_date'])
    player_index['end_date'] = pd.to_datetime(player_index['end_date'])
    valuations['date'] = pd.to_datetime(valuations['date'])
    
    # Initialize new columns
    player_index['start_value'] = None
    player_index['peak_value'] = None
    player_index['end_value'] = None
    
    # For each player record
    for idx, player in player_index.iterrows():
        # Get all valuations for this player
        player_vals = valuations[valuations['player_id'] == player['player_id']]
        
        if len(player_vals) > 0:
            # Get start value (closest date before start_date)
            start_vals = player_vals[player_vals['date'] <= player['start_date']]
            if len(start_vals) > 0:
                start_value = start_vals.iloc[start_vals['date'].argmax()]['market_value_in_eur']
                player_index.at[idx, 'start_value'] = start_value
            
            # Get end value (closest date before end_date)
            end_vals = player_vals[player_vals['date'] <= player['end_date']]
            if len(end_vals) > 0:
                end_value = end_vals.iloc[end_vals['date'].argmax()]['market_value_in_eur']
                player_index.at[idx, 'end_value'] = end_value
            
            # Get peak value (highest value between start and end dates)
            period_vals = player_vals[
                (player_vals['date'] >= player['start_date']) & 
                (player_vals['date'] <= player['end_date'])
            ]
            if len(period_vals) > 0:
                peak_value = period_vals['market_value_in_eur'].max()
                player_index.at[idx, 'peak_value'] = peak_value
    
    # Save updated dataframe back to CSV
    player_index.to_csv('data/trans/player_index.csv', index=False)
    
    return player_index

# Add this part at the bottom of the file
if __name__ == "__main__":
    # Create the trans directory if it doesn't exist
    import os
    os.makedirs('data/trans', exist_ok=True)
    
    # Clean pl_clubs first
    clean_pl_clubs()
    
    # Then create and clean the manager history file
    create_manager_history()
    clean_manager_history()
    
    # Add the dates to manager history
    fetch_manager_dates()
    
    # Create the player index
    create_player_index()
    
    # Create player-manager relationships
    create_player_manager_relationships()
    
    # Add player valuations
    add_player_valuations()