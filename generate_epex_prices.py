"""
Generate realistic EPEX SPOT day-ahead electricity prices for Germany.
Simulates hourly prices for 2023, 2024, and 2025 with realistic patterns.
"""

import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_epex_prices(year):
    """
    Generate realistic EPEX SPOT day-ahead prices for Germany.
    
    Patterns included:
    - Daily cycles (low at night, high during day)
    - Weekly cycles (lower on weekends)
    - Seasonal variations (higher in winter)
    - Renewable production impact (negative prices possible)
    - Price spikes during extreme events
    - Trend towards lower prices over years
    """
    prices = []
    
    # Base price parameters (€/MWh)
    base_price = 80.0  # Average base price
    
    # Year-specific adjustments (energy transition = lower prices over time)
    year_adjustment = {
        2023: 1.15,  # Higher due to energy crisis aftermath
        2024: 1.0,   # Normalization
        2025: 0.92   # Lower due to more renewables
    }
    base_price *= year_adjustment.get(year, 1.0)
    
    current_time = datetime(year, 1, 1, 0, 0)
    end_time = datetime(year + 1, 1, 1, 0, 0)
    
    # Seed for reproducibility but with year variation
    random.seed(year)
    
    # Weather/market state (persists across hours)
    market_stress = 0.0  # -1 to 1, affects volatility
    
    while current_time < end_time:
        day_of_year = current_time.timetuple().tm_yday
        hour = current_time.hour
        day_of_week = current_time.weekday()  # 0=Monday, 6=Sunday
        
        # === SEASONAL COMPONENT ===
        # Higher prices in winter (heating), lower in summer
        seasonal_factor = 1.0 + 0.3 * math.cos(2 * math.pi * (day_of_year - 15) / 365)
        
        # === DAILY COMPONENT ===
        # Price curve throughout the day
        if 0 <= hour < 6:  # Night: low demand, often high wind
            daily_factor = 0.6 + 0.1 * math.sin(hour * math.pi / 6)
        elif 6 <= hour < 9:  # Morning ramp: increasing demand
            daily_factor = 0.7 + 0.4 * (hour - 6) / 3
        elif 9 <= hour < 12:  # Morning peak
            daily_factor = 1.1 + 0.1 * math.sin((hour - 9) * math.pi / 3)
        elif 12 <= hour < 15:  # Midday: high solar production
            daily_factor = 0.95 - 0.15 * math.sin((hour - 12) * math.pi / 3)
        elif 15 <= hour < 20:  # Evening peak: highest prices
            daily_factor = 1.0 + 0.3 * math.sin((hour - 15) * math.pi / 5)
        else:  # Evening decline
            daily_factor = 1.1 - 0.3 * (hour - 20) / 4
        
        # === WEEKLY COMPONENT ===
        # Lower demand on weekends
        if day_of_week >= 5:  # Saturday, Sunday
            weekly_factor = 0.85
        else:
            weekly_factor = 1.0
        
        # === RENEWABLE PRODUCTION IMPACT ===
        # High wind/solar can push prices down or negative
        
        # Wind production (higher in winter, variable)
        wind_factor = 0.5 + 0.3 * math.cos(2 * math.pi * (day_of_year - 15) / 365)
        wind_variation = random.uniform(0.3, 1.0)
        wind_production = wind_factor * wind_variation
        
        # Solar production (only during day, higher in summer)
        if 6 <= hour <= 20:
            solar_factor = 0.3 + 0.4 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
            solar_curve = math.sin((hour - 6) * math.pi / 14)
            solar_production = solar_factor * solar_curve * random.uniform(0.7, 1.0)
        else:
            solar_production = 0
        
        # Combined renewable impact
        renewable_impact = wind_production + solar_production
        
        # High renewables can push prices down significantly
        if renewable_impact > 1.2:
            renewable_factor = 0.3  # Very low prices
        elif renewable_impact > 0.9:
            renewable_factor = 0.6
        else:
            renewable_factor = 1.0 - renewable_impact * 0.3
        
        # === MARKET STRESS / VOLATILITY ===
        # Simulate market conditions (supply/demand imbalances)
        market_stress += random.uniform(-0.1, 0.1)
        market_stress = max(-1.0, min(1.0, market_stress))
        
        stress_factor = 1.0 + market_stress * 0.4
        
        # === EXTREME EVENTS ===
        # Occasional price spikes or negative prices
        extreme_event = random.random()
        
        if extreme_event < 0.001:  # 0.1% chance: major spike
            spike_multiplier = random.uniform(2.5, 4.0)
        elif extreme_event < 0.005:  # 0.5% chance: moderate spike
            spike_multiplier = random.uniform(1.5, 2.5)
        else:
            spike_multiplier = 1.0
        
        # === CALCULATE FINAL PRICE ===
        price = (base_price * 
                seasonal_factor * 
                daily_factor * 
                weekly_factor * 
                renewable_factor * 
                stress_factor * 
                spike_multiplier)
        
        # Add random noise
        noise = random.uniform(-5, 5)
        price += noise
        
        # Negative prices possible during very high renewable production
        # More common at night with high wind, or midday with high solar
        if renewable_impact > 1.3:
            if (2 <= hour <= 5) or (11 <= hour <= 14):  # Night wind or midday solar
                if random.random() < 0.4:  # 40% chance of negative price
                    price = random.uniform(-80, -5)
        elif renewable_impact > 1.1 and (2 <= hour <= 4):
            if random.random() < 0.15:  # 15% chance
                price = random.uniform(-30, -2)
        
        # Round to 2 decimals
        price = round(price, 2)
        
        # Store result
        prices.append({
            "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "price_eur_mwh": price,
            "price_eur_kwh": round(price / 1000, 5)
        })
        
        # Move to next hour
        current_time += timedelta(hours=1)
    
    return prices


def calculate_statistics(prices):
    """Calculate price statistics."""
    values = [p["price_eur_mwh"] for p in prices]
    
    return {
        "count": len(values),
        "mean": round(sum(values) / len(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "negative_hours": sum(1 for v in values if v < 0),
        "negative_percentage": round(sum(1 for v in values if v < 0) / len(values) * 100, 2)
    }


if __name__ == "__main__":
    print("Generating EPEX SPOT day-ahead prices for Germany...\n")
    print("=" * 70)
    
    output_dir = Path("data/prices")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_years_data = []
    
    for year in [2023, 2024, 2025]:
        print(f"\nGenerating prices for {year}...")
        
        prices = generate_epex_prices(year)
        stats = calculate_statistics(prices)
        
        print(f"  Hours: {stats['count']}")
        print(f"  Average: €{stats['mean']:.2f}/MWh")
        print(f"  Min: €{stats['min']:.2f}/MWh")
        print(f"  Max: €{stats['max']:.2f}/MWh")
        print(f"  Negative hours: {stats['negative_hours']} ({stats['negative_percentage']}%)")
        
        # Add to combined dataset
        all_years_data.extend(prices)
        
        # Save individual year
        year_file = output_dir / f"epex_dayahead_{year}.json"
        with open(year_file, 'w', encoding='utf-8') as f:
            json.dump({
                "source": "EPEX SPOT Day-Ahead",
                "market": "Germany",
                "year": year,
                "currency": "EUR",
                "unit": "MWh",
                "statistics": stats,
                "data": prices
            }, f, indent=2)
        
        print(f"  ✓ Saved to {year_file}")
    
    # Save combined file
    combined_file = output_dir / "epex_dayahead_2023_2025.json"
    combined_stats = calculate_statistics(all_years_data)
    
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump({
            "source": "EPEX SPOT Day-Ahead",
            "market": "Germany",
            "years": [2023, 2024, 2025],
            "currency": "EUR",
            "unit": "MWh",
            "description": "Simulated hourly day-ahead electricity prices for Germany",
            "statistics": combined_stats,
            "data": all_years_data
        }, f, indent=2)
    
    print("\n" + "=" * 70)
    print(f"Combined file saved to {combined_file}")
    print(f"\nOverall statistics (2023-2025):")
    print(f"  Total hours: {combined_stats['count']}")
    print(f"  Average: €{combined_stats['mean']:.2f}/MWh (€{combined_stats['mean']/1000:.5f}/kWh)")
    print(f"  Min: €{combined_stats['min']:.2f}/MWh")
    print(f"  Max: €{combined_stats['max']:.2f}/MWh")
    print(f"  Negative hours: {combined_stats['negative_hours']} ({combined_stats['negative_percentage']}%)")
    print("\nAll EPEX price data generated successfully!")
