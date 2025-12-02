from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict


def aggregate_by_month(data: List[Dict], year: Optional[int] = None) -> List[Dict]:
    """
    Aggregate time series data by month in time series format.
    
    Args:
        data: List of dicts with 'timestamp' and 'value' keys
        year: Optional year filter
    
    Returns:
        List of dicts with timestamp (first day of month) and value (total kWh)
    """
    monthly_data = defaultdict(lambda: {"values": [], "month": None, "year": None})

    for item in data:
        timestamp_str = item.get("timestamp", "")
        value_str = item.get("value", "0")

        try:
            # Parse timestamp
            if "T" in timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace("Z", ""))
            else:
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            # Filter by year if specified
            if year and dt.year != year:
                continue

            # Convert value to float
            try:
                value = float(value_str)
            except (ValueError, TypeError):
                continue

            # Group by year-month
            key = (dt.year, dt.month)
            monthly_data[key]["values"].append(value)
            monthly_data[key]["month"] = dt.month
            monthly_data[key]["year"] = dt.year

        except (ValueError, AttributeError):
            continue

    # Calculate aggregations in time series format
    result = []
    for (year_key, month_key), month_info in sorted(monthly_data.items()):
        values = month_info["values"]
        if values:
            # Sum values and convert from kW to kWh
            # Each 15-minute interval represents 0.25 hours
            total_kwh = sum(values) * 0.25

            # Create timestamp for first day of month
            timestamp = datetime(year_key, month_key, 1).strftime("%Y-%m-%dT%H:%M:%S")

            result.append({"timestamp": timestamp, "value": round(total_kwh, 2)})

    return result


def aggregate_by_day(
    data: List[Dict], year: Optional[int] = None, month: Optional[int] = None
) -> List[Dict]:
    """
    Aggregate time series data by day in time series format.
    
    Args:
        data: List of dicts with 'timestamp' and 'value' keys
        year: Optional year filter
        month: Optional month filter (1-12)
    
    Returns:
        List of dicts with timestamp (start of day) and value (total kWh)
    """
    daily_data = defaultdict(lambda: {"values": []})

    for item in data:
        timestamp_str = item.get("timestamp", "")
        value_str = item.get("value", "0")

        try:
            # Parse timestamp
            if "T" in timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace("Z", ""))
            else:
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            # Filter by year if specified
            if year and dt.year != year:
                continue

            # Filter by month if specified
            if month and dt.month != month:
                continue

            # Convert value to float
            try:
                value = float(value_str)
            except (ValueError, TypeError):
                continue

            # Group by year-month-day
            key = (dt.year, dt.month, dt.day)
            daily_data[key]["values"].append(value)

        except (ValueError, AttributeError):
            continue

    # Calculate aggregations in time series format
    result = []
    for (year_key, month_key, day_key), day_info in sorted(daily_data.items()):
        values = day_info["values"]
        if values:
            # Sum values and convert from kW to kWh
            # Each 15-minute interval represents 0.25 hours
            total_kwh = sum(values) * 0.25

            # Create timestamp for start of day
            timestamp = datetime(year_key, month_key, day_key).strftime(
                "%Y-%m-%dT%H:%M:%S"
            )

            result.append({"timestamp": timestamp, "value": round(total_kwh, 2)})

    return result
