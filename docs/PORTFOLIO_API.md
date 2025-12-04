# Portfolio API Documentation

## Overview

The Portfolio API allows users to view and track their renewable energy investments, including shares owned, current values, gains/losses, and production data.

## Endpoints

### GET /portfolio/{user_id}

Get complete portfolio information for a user.

**Parameters:**
- `user_id` (path, required): User identifier (e.g., "user_001")
- `include_production` (query, optional): Include production data (default: true)
- `period` (query, optional): Time period for calculations (default: "ytd")
  - `ytd`: Year to date
  - `1m`: Last 30 days
  - `3m`: Last 90 days
  - `6m`: Last 180 days
  - `1y`: Last 365 days
  - `all`: All time

**Example Request:**
```bash
GET /portfolio/user_001?period=ytd&include_production=true
```

**Example Response:**
```json
{
  "user_id": "user_001",
  "user_name": "Marie Dupont",
  "pod_id": "000011",
  "registration_date": "2024-03-15",
  "period": {
    "type": "ytd",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-04T20:00:00",
    "days": 338
  },
  "summary": {
    "total_projects": 3,
    "total_shares": 9,
    "total_investment": 10500.00,
    "current_value": 10640.00,
    "total_gain_loss": 140.00,
    "total_gain_loss_percentage": 1.33,
    "total_production_kwh": 8450.50,
    "estimated_annual_savings": 2280.75,
    "payback_years": 4.60
  },
  "by_energy_type": {
    "wind": {
      "shares": 5,
      "investment": 4250.00,
      "capacity": 7.5,
      "production_kwh": 5200.30
    },
    "solar": {
      "shares": 3,
      "investment": 3750.00,
      "capacity": 7.5,
      "production_kwh": 3250.20
    },
    "battery": {
      "shares": 1,
      "investment": 2500.00,
      "capacity": 10.0,
      "production_kwh": 0
    }
  },
  "investments": [
    {
      "project_id": "00003",
      "project_name": "Erpeldange Wind Farm",
      "energy_type": "wind",
      "shares": 5,
      "capacity": 7.5,
      "capacity_unit": "kW",
      "purchase_date": "2024-06-01",
      "days_held": 186,
      "investment": {
        "purchase_price_per_share": 850.00,
        "total_investment": 4250.00,
        "current_price_per_share": 865.00,
        "current_value": 4325.00,
        "gain_loss": 75.00,
        "gain_loss_percentage": 1.76,
        "annualized_return": 3.46
      },
      "production": {
        "total_kwh": 5200.30,
        "data_points": 16128,
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-12-04T20:00:00"
      }
    }
  ]
}
```

### GET /portfolio/{user_id}/production

Get detailed production time series for user's portfolio (future enhancement).

**Parameters:**
- `user_id` (path, required): User identifier
- `start_date` (query, optional): Start date (ISO format)
- `end_date` (query, optional): End date (ISO format)
- `aggregation` (query, optional): Time aggregation (hourly, daily, monthly)

## Response Fields

### Summary Section

- `total_projects`: Number of different projects invested in
- `total_shares`: Total number of shares across all projects
- `total_investment`: Total amount invested (€)
- `current_value`: Current market value of all investments (€)
- `total_gain_loss`: Unrealized gain or loss (€)
- `total_gain_loss_percentage`: Percentage gain/loss (%)
- `total_production_kwh`: Total energy produced in period (kWh)
- `estimated_annual_savings`: Projected annual savings (€)
- `payback_years`: Estimated years to recover investment

### By Energy Type

Breakdown of investments by technology:
- `shares`: Number of shares
- `investment`: Total invested (€)
- `capacity`: Total capacity (kW or kWh)
- `production_kwh`: Total production (kWh)

### Investment Details

For each investment:
- **Project Info**: ID, name, energy type
- **Holdings**: Shares, capacity
- **Purchase Info**: Date, days held
- **Financial Performance**:
  - Purchase and current prices
  - Gain/loss (absolute and percentage)
  - Annualized return
- **Production**: Total kWh produced in period

## Sample Users

### user_001 - Marie Dupont
- **POD**: 000011
- **Investments**: 3 projects (Wind, Solar, Battery)
- **Total Investment**: €10,500
- **Profile**: Balanced portfolio with diversification

### user_002 - Jean Schmidt
- **POD**: 00012
- **Investments**: 2 projects (Wind, Solar)
- **Total Investment**: €13,600
- **Profile**: Focus on production assets

### user_003 - Sophie Weber
- **POD**: 00011
- **Investments**: 3 projects (Solar, Wind, Battery)
- **Total Investment**: €34,300
- **Profile**: Large investor with significant holdings

## Use Cases

### 1. Portfolio Dashboard
```bash
curl http://localhost:8000/portfolio/user_001
```
Display user's complete portfolio with current performance.

### 2. Year-to-Date Performance
```bash
curl http://localhost:8000/portfolio/user_001?period=ytd
```
Show performance since January 1st.

### 3. Monthly Review
```bash
curl http://localhost:8000/portfolio/user_001?period=1m
```
Review last 30 days of production and performance.

### 4. Quick Summary (No Production)
```bash
curl http://localhost:8000/portfolio/user_001?include_production=false
```
Fast response with just financial data.

## Calculations

### Gain/Loss
```
Gain/Loss = (Current Value - Purchase Price) × Shares
Gain/Loss % = (Gain/Loss / Total Investment) × 100
```

### Annualized Return
```
Annualized Return = (Gain/Loss % / Days Held) × 365
```

### Production Value
```
Self-Consumption Value = Production × 50% × Electricity Price
Export Value = Production × 50% × Feed-in Tariff
Total Value = Self-Consumption Value + Export Value
```

### Payback Period
```
Annual Savings = Production Value + Asset Appreciation
Payback Years = Total Investment / Annual Savings
```

## Integration with Other APIs

### Combined with Optimization
1. Get user's portfolio: `GET /portfolio/{user_id}`
2. Get user's consumption: `GET /loadcurve/{pod_id}`
3. Optimize additional investments: `POST /optimize`

### Production Analysis
1. Get portfolio production: `GET /portfolio/{user_id}`
2. Compare with consumption: `GET /loadcurve/{pod_id}/monthly`
3. Calculate self-consumption rate

## Future Enhancements

### Planned Features
- [ ] Detailed production time series endpoint
- [ ] Transaction history (buy/sell)
- [ ] Dividend/revenue tracking
- [ ] Tax reporting exports
- [ ] Performance benchmarking
- [ ] Portfolio rebalancing suggestions
- [ ] Real-time market values
- [ ] Alerts and notifications

### Advanced Analytics
- [ ] Risk metrics (volatility, Sharpe ratio)
- [ ] Correlation analysis
- [ ] Scenario modeling
- [ ] Weather impact analysis
- [ ] Grid price optimization

## Error Responses

### 404 - Portfolio Not Found
```json
{
  "detail": "Portfolio not found for user: user_999"
}
```

### 500 - Server Error
```json
{
  "detail": "Error retrieving portfolio: [error message]"
}
```

## Best Practices

1. **Cache Results**: Portfolio calculations can be cached for 5-15 minutes
2. **Pagination**: For large portfolios, consider pagination
3. **Async Loading**: Load financial data first, then production data
4. **Period Selection**: Use appropriate periods for different views
5. **Error Handling**: Always handle missing production data gracefully
