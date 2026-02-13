"""
Generate production profiles for all renewable energy projects.
Creates realistic 2-year (2023-2024) production data for each project.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import math
import random


def generate_solar_production(capacity_kwc, year=2023, location_factor=1.0, efficiency=0.21):
    """Generate solar production with location-specific adjustments."""
    production_data = []
    current_time = datetime(year, 1, 1, 0, 0)
    end_time = datetime(year + 1, 1, 1, 0, 0)
    interval = timedelta(minutes=15)
    
    random.seed(year + int(capacity_kwc * 100))
    cloud_cover = 0.2
    
    while current_time < end_time:
        day_of_year = current_time.timetuple().tm_yday
        hour = current_time.hour
        minute = current_time.minute
        hour_decimal = hour + minute / 60.0
        
        solar_noon = 13.0
        day_length_variation = 4.5 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
        sunrise_hour = solar_noon - (6 + day_length_variation)
        sunset_hour = solar_noon + (6 + day_length_variation)
        
        production = 0.0
        
        if sunrise_hour <= hour_decimal <= sunset_hour:
            hours_from_noon = abs(hour_decimal - solar_noon)
            day_half_length = 6 + day_length_variation
            
            if day_half_length > 0:
                sun_angle = math.cos(math.pi * hours_from_noon / (day_half_length * 1.2))
                sun_angle = max(0, sun_angle)
                
                seasonal_factor = 0.4 + 0.6 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
                seasonal_factor = max(0.3, seasonal_factor)
                
                production = capacity_kwc * sun_angle * seasonal_factor * location_factor
                
                # Weather variation
                cloud_cover += random.uniform(-0.02, 0.02)
                cloud_cover = max(0, min(0.9, cloud_cover))
                
                seasonal_cloud_bias = 0.15 * math.cos(2 * math.pi * (day_of_year - 80) / 365)
                cloud_cover_adjusted = max(0, min(1, cloud_cover + seasonal_cloud_bias))
                
                cloud_factor = 1.0 - (cloud_cover_adjusted ** 1.5)
                micro_variation = random.uniform(0.92, 1.08)
                temp_factor = 1.0 - 0.05 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
                
                production *= cloud_factor * micro_variation * temp_factor
                
                if random.random() < 0.001:
                    cloud_cover = random.uniform(0.6, 0.9)
                if random.random() < 0.0005:
                    cloud_cover = random.uniform(0.0, 0.1)
                
                production = max(0, production)
        
        production = round(production, 4)
        timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        production_data.append({"timestamp": timestamp, "value": production})
        current_time += interval
    
    return production_data


def generate_wind_production(capacity_kw, year=2023, capacity_factor=0.28):
    """Generate wind production with capacity factor adjustment."""
    production_data = []
    current_time = datetime(year, 1, 1, 0, 0)
    end_time = datetime(year + 1, 1, 1, 0, 0)
    interval = timedelta(minutes=15)
    
    while current_time < end_time:
        day_of_year = current_time.timetuple().tm_yday
        hour = current_time.hour
        minute = current_time.minute
        
        # Adjust base wind for capacity factor
        base_wind_adjustment = capacity_factor / 0.28  # Normalize to default
        
        seasonal_factor = (0.6 + 0.4 * math.cos(2 * math.pi * (day_of_year - 15) / 365)) * base_wind_adjustment
        daily_factor = 0.95 + 0.05 * math.cos(2 * math.pi * (hour - 3) / 24)
        
        time_index = day_of_year * 96 + hour * 4 + minute // 15
        
        wind_variation = (
            0.4 * math.sin(time_index * 0.01) +
            0.3 * math.sin(time_index * 0.005 + 1.5) +
            0.2 * math.sin(time_index * 0.002 + 3.0) +
            0.1 * math.sin(time_index * 0.001 + 2.0)
        )
        
        wind_factor = (wind_variation + 1) / 2
        wind_factor = max(0, min(1, wind_factor))
        wind_factor *= seasonal_factor * daily_factor
        
        if wind_factor < 0.2:
            production = 0
        elif wind_factor > 0.92:
            production = 0
        elif wind_factor > 0.5:
            production = capacity_kw * (0.85 + 0.1 * (wind_factor - 0.5) / 0.42)
        else:
            normalized = (wind_factor - 0.2) / (0.5 - 0.2)
            production = capacity_kw * (normalized ** 2.2)
        
        production = round(production, 4)
        timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        production_data.append({"timestamp": timestamp, "value": production})
        current_time += interval
    
    return production_data


def generate_battery_profile(year=2023):
    """Generate battery profile (zeros)."""
    production_data = []
    current_time = datetime(year, 1, 1, 0, 0)
    end_time = datetime(year + 1, 1, 1, 0, 0)
    interval = timedelta(minutes=15)
    
    while current_time < end_time:
        timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%S")
        production_data.append({"timestamp": timestamp, "value": 0.0})
        current_time += interval
    
    return production_data


# Project configurations
projects = {
    "00001": {"type": "battery", "capacity": 10},
    "00002": {"type": "solar", "capacity": 2.5, "location_factor": 1.0},
    "00003": {"type": "wind", "capacity": 1.5, "capacity_factor": 0.28},
    "00004": {"type": "solar", "capacity": 2.0, "location_factor": 0.95},  # City center, some shading
    "00005": {"type": "battery", "capacity": 25},
    "00006": {"type": "wind", "capacity": 2.0, "capacity_factor": 0.32},  # Better location
    "00007": {"type": "solar", "capacity": 1.5, "location_factor": 0.92},  # Agrivoltaic, semi-transparent
    "00008": {"type": "battery", "capacity": 5},
    "00009": {"type": "solar", "capacity": 3.2, "location_factor": 1.05},  # Factory, optimal orientation
    "00010": {"type": "wind", "capacity": 3.0, "capacity_factor": 0.35},  # Mountain, excellent wind
}

if __name__ == "__main__":
    print("Generating production profiles for all projects (2023-2024)...\n")
    print("=" * 70)
    
    output_dir = Path("data/projects/production")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for project_id, config in projects.items():
        print(f"\nProject {project_id} ({config['type'].upper()}):")
        
        if config["type"] == "battery":
            print(f"  Generating battery profile (capacity: {config['capacity']} kWh)...")
            data_2023 = generate_battery_profile(2023)
            data_2024 = generate_battery_profile(2024)
            
        elif config["type"] == "solar":
            capacity = config["capacity"]
            location_factor = config.get("location_factor", 1.0)
            print(f"  Generating solar profile (capacity: {capacity} kWc, location factor: {location_factor})...")
            data_2023 = generate_solar_production(capacity, 2023, location_factor)
            data_2024 = generate_solar_production(capacity, 2024, location_factor)
            
        elif config["type"] == "wind":
            capacity = config["capacity"]
            capacity_factor = config.get("capacity_factor", 0.28)
            print(f"  Generating wind profile (capacity: {capacity} kW, capacity factor: {capacity_factor})...")
            data_2023 = generate_wind_production(capacity, 2023, capacity_factor)
            data_2024 = generate_wind_production(capacity, 2024, capacity_factor)
        
        # Combine years
        data_combined = data_2023 + data_2024
        
        # Save
        output_file = output_dir / f"{project_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_combined, f, indent=2)
        
        # Statistics
        if config["type"] != "battery":
            values = [item["value"] for item in data_combined]
            total_kwh = sum(values) * 0.25
            avg_kw = sum(values) / len(values)
            max_kw = max(values)
            
            print(f"  ✓ Saved {len(data_combined)} data points")
            print(f"  Total production: {total_kwh:,.2f} kWh")
            print(f"  Average: {avg_kw:.4f} kW")
            print(f"  Peak: {max_kw:.4f} kW")
        else:
            print(f"  ✓ Saved {len(data_combined)} data points (battery storage)")
    
    print("\n" + "=" * 70)
    print("All production profiles generated successfully!")
    print(f"\nFiles created in: {output_dir}")
