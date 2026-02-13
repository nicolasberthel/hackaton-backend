import json
from datetime import datetime, timedelta
from pathlib import Path

def generate_battery_profile(year=2023):
    """
    Generate a battery storage profile.
    Battery doesn't produce energy, but stores and releases it.
    For optimization purposes, we'll create a flat profile representing storage capacity.
    
    Args:
        year: Year for the simulation
    
    Returns:
        List of dicts with timestamp and value (always 0 for battery)
    """
    production_data = []
    
    # Start from January 1st at 00:00
    current_time = datetime(year, 1, 1, 0, 0)
    end_time = datetime(year + 1, 1, 1, 0, 0)
    
    # 15-minute interval
    interval = timedelta(minutes=15)
    
    while current_time < end_time:
        # Battery doesn't produce, it stores
        # We'll use 0 for production profile
        # The optimization algorithm will handle battery separately
        timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        production_data.append({
            "timestamp": timestamp,
            "value": 0.0
        })
        
        current_time += interval
    
    return production_data


if __name__ == "__main__":
    print("Generating battery storage profile for 2023-2024...")
    
    # Generate battery profile for both years (all zeros since battery stores, doesn't produce)
    data_2023 = generate_battery_profile(year=2023)
    data_2024 = generate_battery_profile(year=2024)
    data_combined = data_2023 + data_2024
    
    print(f"Generated {len(data_combined)} data points (2 years)")
    
    # Create output directory
    output_dir = Path("data/projects/production")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON file - using 00001 for battery project
    output_file = output_dir / "00001.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_combined, f, indent=2)
    
    print(f"Battery profile saved to {output_file}")
    print("\nNote: Battery storage has 0 production values.")
    print("Battery optimization requires special handling in the algorithm.")
