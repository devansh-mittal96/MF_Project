import os
import requests
import pandas as pd

def fetch_live_nav():
    raw_path = "./data/raw/"
    os.makedirs(raw_path, exist_ok=True)
    
    key_schemes = {
        "SBI_Bluechip": "119551",
        "ICICI_Bluechip": "120503",
        "Nippon_Large_Cap": "118632",
        "Axis_Bluechip": "119092",
        "Kotak_Bluechip": "120841"
    }
    
    print("🚀 Starting Live NAV Fetch...")
    for fund_name, code in key_schemes.items():
        url = f"https://api.mfapi.in/mf/{code}"
        res = requests.get(url)
        
        if res.status_code == 200:
            data_json = res.json()
            df_temp = pd.DataFrame(data_json['data'])
            file_name = os.path.join(raw_path, f"{fund_name}_live.csv")
            df_temp.to_csv(file_name, index=False)
            print(f"Saved successfully: {file_name}")
        else:
            print(f"Failed to fetch data for {fund_name}")

if __name__ == "__main__":
    fetch_live_nav()