"""
Automatically fetch complete load profile from live service.
"""

import requests
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
import time


# API Configuration
BASE_URL = "https://mule-profile-api.private.enocloud.eu/api/v1/profiles"
CLIENT_ID = "6e80ba5bce2b4a41be20076389dcb495"
CLIENT_SECRET = "fEF4Ba8AB598439e974E132e6d70f9B1"

HEADERS = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "Content-Type": "application/json"
}


def get_source_for_date(date):
    """Determine source (sap or ods) based on date."""
    # Try SAP for all dates first
    return "sap"


def fetch_monthly_profile(pod, obis, year, month):
    """Fetch profile data for a specific month."""
    from_date = datetime(year, month, 1)
    
    if month == 12:
        to_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        to_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    source = get_source_for_date(from_date)
    from_date_str = from_date.strftime("%Y-%m-%d")
    to_date_str = to_date.strftime("%Y-%m-%d")
    
    url = f"{BASE_URL}/{pod}/{obis}"
    params = {
        "source": source,
        "from_date": from_date_str,
        "to_date": to_date_str,
        "unit": "kwh"
    }
    
    print(f"  {year}-{month:02d} (source: {source})...", end=" ", flush=True)
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ {len(data.get('values', []))} points")
            return data
        else:
            print(f"✗ Error {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ {str(e)}")
        return None


def build_profile_csv(pod, obis, start_year, start_month, end_date=None, output_filename=None, convert_to_json=False, json_divider=1):
    """Build complete CSV profile.
    
    Args:
        pod: POD identifier
        obis: OBIS code
        start_year: Start year
        start_month: Start month
        end_date: End date (default: now)
        output_filename: Output CSV filename
        convert_to_json: If True, also create JSON file in data/projects/production/
        json_divider: Divider to apply to values in JSON (default: 1, no division)
    """
    if end_date is None:
        end_date = datetime.now()
    
    print(f"\nFetching profile: {pod}")
    print(f"OBIS: {obis}")
    print(f"Period: {start_year}-{start_month:02d} to {end_date.strftime('%Y-%m-%d')}")
    print("=" * 70)
    
    all_data = []
    current_date = datetime(start_year, start_month, 1)
    
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        
        monthly_data = fetch_monthly_profile(pod, obis, year, month)
        
        if monthly_data and 'values' in monthly_data:
            for item in monthly_data['values']:
                timestamp = item.get('ts', '')
                value = item.get('value', 0)
                
                try:
                    if 'T' in timestamp:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '').split('+')[0])
                    else:
                        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    
                    formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                    all_data.append({'timestamp': formatted_timestamp, 'value': value})
                except:
                    continue
        
        if month == 12:
            current_date = datetime(year + 1, 1, 1)
        else:
            current_date = datetime(year, month + 1, 1)
        
        time.sleep(0.3)
    
    all_data.sort(key=lambda x: x['timestamp'])
    
    output_dir = Path("data/profiles")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if output_filename:
        output_file = output_dir / output_filename
    else:
        pod_short = pod[-10:]
        output_file = output_dir / f"LU_ENO_DELPHI_LU_virtual_ind_{pod_short}.csv"
    
    print(f"\nWriting {len(all_data)} points to {output_file}...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['timestamp', 'value'])
        for item in all_data:
            writer.writerow([item['timestamp'], item['value']])
    
    if all_data:
        values = [float(item['value']) for item in all_data]
        total_kwh = sum(values) * 0.25
        
        print(f"\n✓ Profile saved!")
        print(f"  Data points: {len(all_data)}")
        print(f"  Period: {all_data[0]['timestamp']} to {all_data[-1]['timestamp']}")
        print(f"  Total: {total_kwh:,.2f} kWh")
        print(f"  Average: {sum(values) / len(values):.4f} kW")
        print(f"  Max: {max(values):.4f} kW")
    
    # Optional JSON conversion
    json_file = None
    if convert_to_json and all_data:
        # Extract project number from filename (e.g., "00011" from "...00011.csv")
        import re
        match = re.search(r'(\d{5})\.csv$', output_filename)
        if match:
            project_num = match.group(1)
            json_output_dir = Path("data/projects/production")
            json_output_dir.mkdir(parents=True, exist_ok=True)
            json_file = json_output_dir / f"{project_num}.json"
            
            json_data = []
            for item in all_data:
                timestamp = item['timestamp'].replace(' ', 'T')
                value = float(item['value']) / json_divider
                json_data.append({
                    "timestamp": timestamp,
                    "value": value
                })
            
            with open(json_file, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            json_values = [item['value'] for item in json_data]
            print(f"\n✓ JSON file created!")
            print(f"  File: {json_file}")
            print(f"  Divider applied: {json_divider}")
            print(f"  Average: {sum(json_values)/len(json_values):.4f} kW")
            print(f"  Max: {max(json_values):.4f} kW")
            print(f"  Total: {sum(json_values) * 0.25:,.2f} kWh")
    
    return output_file, json_file if convert_to_json else output_file


if __name__ == "__main__":
    #POD = "LU0000010721700000000000070042775"
    #POD = "LU0000010916400000000000040688845"
    #POD = "LU0000010937800000000000040688417"
    #POD = "LU0000010344200000000000070078267"
    POD = "LU0000010356800000000000070053380"
    #OBIS = "1-1:2.29.0"
    OBIS = "1-1:1.29.0"
    
    print("Fetching complete load profile from live service...")
    
    # Example 1: CSV only
    # output_file = build_profile_csv(POD, OBIS, 2023, 1, output_filename="LU_ENO_DELPHI_LU_virtual_ind_00013.csv")
    
    # Example 2: CSV + JSON with divider
    output_file = build_profile_csv(
        POD, OBIS, 2023, 1, 
        output_filename="LU_ENO_DELPHI_LU_virtual_ind_00002.csv",
        convert_to_json=False,
        json_divider=1
    )
    
    print(f"\n✓ Complete! File: {output_file}")
