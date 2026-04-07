import fastf1
import pandas as pd
import json
import os

if not os.path.exists('f1_cache'):
    os.makedirs('f1_cache')
fastf1.Cache.enable_cache('f1_cache')

def get_teammate_data():
    print("Loading 2021 Silverstone Race for F1-Pulse")
    session = fastf1.get_session(2021, 'Silverstone', 'R')
    session.load()

    # Mercedes Teammates
    drivers = ['HAM', 'BOT']
    laps_to_get = 10
    all_data = []

    for drv in drivers:
        print(f"Fetching first {laps_to_get} laps for {drv}...")
        laps = session.laps.pick_driver(drv).pick_laps(range(1, laps_to_get + 1))
        tel = laps.get_telemetry()
        
        df = tel[['Date', 'Speed', 'RPM', 'nGear', 'Throttle', 'Brake']].copy()
        df['Driver'] = drv
        all_data.append(df)

    print("Interleaving driver data...")
    combined = pd.concat(all_data).sort_values(by='Date')
    combined['Date'] = combined['Date'].astype(str)
    combined.dropna(inplace=True)
    
    combined.to_json('telemetry.json', orient='records', indent=2)
    print(f"Created telemetry.json with {len(combined)} rows.")

if __name__ == "__main__":
    get_teammate_data()