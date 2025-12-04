# Portfolio API Setup Complete

## Overview

The Portfolio API provides comprehensive investment tracking for users who have purchased shares in renewable energy projects. It shows holdings, performance, production, and financial metrics.

## What Was Created

### 1. API Endpoint
**GET /portfolio/{user_id}**
- Complete portfolio overview
- Financial performance (gains/losses)
- Production data by project
- Aggregated metrics by energy type
- Flexible time period filtering

### 2. Sample Data
**data/users/portfolios.json**
- 3 sample users with different investment profiles
- Realistic investment dates and amounts
- Mix of solar, wind, and battery investments

### 3. Sample Users

#### user_001 - Marie Dupont (Balanced Investor)
- **Total Investment**: €10,500
- **Projects**: 3 (Wind, Solar, Battery)
- **Profile**: Diversified portfolio, moderate investment
- **POD**: 000011

#### user_002 - Jean Schmidt (Production Focus)
- **Total Investment**: €13,600
- **Projects**: 2 (Wind, Solar)
- **Profile**: Focus on energy production assets
- **POD**: 00012

#### user_003 - Sophie Weber (Large Investor)
- **Total Investment**: €34,300
- **Projects**: 3 (Solar, Wind, Battery)
- **Profile**: Significant holdings, early adopter
- **POD**: 00011

## API Features

### Financial Metrics
- ✅ Total investment amount
- ✅ Current market value
- ✅ Unrealized gains/losses (€ and %)
- ✅ Annualized return calculation
- ✅ Days held per investment
- ✅ Payback period estimation

### Production Metrics
- ✅ Total kWh produced per project
- ✅ Aggregated production by energy type
- ✅ Flexible time period filtering
- ✅ Production value estimation
- ✅ Annual savings projection

### Portfolio Analytics
- ✅ Breakdown by energy type (solar/wind/battery)
- ✅ Capacity summary (kW/kWh)
- ✅ Share count per project
- ✅ Investment diversification view

## Example Requests

### 1. Get Full Portfolio (Year-to-Date)
```bash
curl http://localhost:8000/portfolio/user_001?period=ytd
```

### 2. Last 30 Days Performance
```bash
curl http://localhost:8000/portfolio/user_001?period=1m
```

### 3. All-Time Performance
```bash
curl http://localhost:8000/portfolio/user_001?period=all
```

### 4. Financial Data Only (Fast)
```bash
curl http://localhost:8000/portfolio/user_001?include_production=false
```

## Response Structure

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
    "wind": {...},
    "solar": {...},
    "battery": {...}
  },
  
  "investments": [...]
}
```

## Key Calculations

### 1. Gain/Loss
```python
gain_loss = (current_price - purchase_price) × shares
gain_loss_pct = (gain_loss / total_investment) × 100
```

### 2. Annualized Return
```python
days_held = today - purchase_date
annualized_return = (gain_loss_pct / days_held) × 365
```

### 3. Production Value
```python
# Assume 50% self-consumption, 50% export
self_consumed = production × 0.5 × electricity_price (€0.30/kWh)
exported = production × 0.5 × feed_in_tariff (€0.05/kWh)
total_value = self_consumed + exported
```

### 4. Payback Period
```python
annual_savings = production_value + asset_appreciation
payback_years = total_investment / annual_savings
```

## Testing

Run the test script:
```bash
python test_portfolio.py
```

Expected output:
```
📊 Testing portfolio for user_001...

✅ Marie Dupont
   POD: 000011
   Registration: 2024-03-15

   💰 Financial Summary:
      Total Investment: €10,500.00
      Current Value: €10,640.00
      Gain/Loss: €140.00 (1.33%)

   ⚡ Energy Summary:
      Projects: 3
      Total Shares: 9
      Production (YTD): 8,450.50 kWh
      Est. Annual Savings: €2,280.75
      Payback Period: 4.6 years
```

## Integration Examples

### 1. User Dashboard
```javascript
// Fetch portfolio
const portfolio = await fetch('/portfolio/user_001?period=ytd');

// Display summary
displayFinancialSummary(portfolio.summary);
displayInvestments(portfolio.investments);
displayProductionChart(portfolio.by_energy_type);
```

### 2. Performance Tracking
```javascript
// Compare periods
const ytd = await fetch('/portfolio/user_001?period=ytd');
const lastMonth = await fetch('/portfolio/user_001?period=1m');

// Calculate trends
const trend = calculateTrend(ytd, lastMonth);
```

### 3. Investment Recommendations
```javascript
// Get current portfolio
const portfolio = await fetch('/portfolio/user_001');

// Get optimization suggestions
const suggestions = await fetch('/optimize', {
  method: 'POST',
  body: JSON.stringify({
    pod_id: portfolio.pod_id,
    budget: 5000
  })
});

// Show rebalancing opportunities
displayRecommendations(suggestions, portfolio);
```

## Use Cases

### 1. Personal Dashboard
- View all investments in one place
- Track performance over time
- Monitor production vs consumption

### 2. Tax Reporting
- Annual gains/losses
- Production income
- Investment cost basis

### 3. Investment Planning
- Current allocation by type
- Diversification analysis
- Rebalancing opportunities

### 4. Performance Analysis
- ROI by project
- Best/worst performers
- Payback progress

## Future Enhancements

### Phase 2 - Transaction History
- [ ] Buy/sell transactions
- [ ] Dividend payments
- [ ] Fee tracking
- [ ] Cost basis adjustments

### Phase 3 - Advanced Analytics
- [ ] Risk metrics (volatility, beta)
- [ ] Benchmark comparison
- [ ] Correlation analysis
- [ ] Monte Carlo simulations

### Phase 4 - Real-Time Features
- [ ] Live market prices
- [ ] Price alerts
- [ ] Production alerts
- [ ] Performance notifications

### Phase 5 - Social Features
- [ ] Portfolio sharing
- [ ] Leaderboards
- [ ] Community insights
- [ ] Investment clubs

## Data Management

### Adding New Users
Edit `data/users/portfolios.json`:
```json
{
  "user_id": "user_004",
  "name": "New User",
  "email": "user@example.lu",
  "pod_id": "00013",
  "registration_date": "2024-12-01",
  "investments": [...]
}
```

### Updating Share Prices
Prices are stored in each investment. In production, these would be:
- Fetched from a pricing service
- Updated daily/hourly
- Based on market conditions
- Calculated from project performance

### Production Data
Production is calculated from project files in `data/projects/production/`.
The API automatically:
- Loads production profiles
- Filters by date range
- Scales by number of shares
- Aggregates across projects

## Best Practices

1. **Caching**: Cache portfolio calculations for 5-15 minutes
2. **Lazy Loading**: Load financial data first, production data async
3. **Error Handling**: Handle missing production data gracefully
4. **Period Selection**: Default to YTD for most views
5. **Performance**: Use `include_production=false` for quick loads

## Documentation

Complete API documentation: `docs/PORTFOLIO_API.md`

## Summary

The Portfolio API is ready to use! It provides:
- ✅ Complete investment tracking
- ✅ Financial performance metrics
- ✅ Production monitoring
- ✅ Flexible time periods
- ✅ Sample data for 3 users
- ✅ Full documentation
- ✅ Test script

Start the server and test with:
```bash
python -m uvicorn main:app --reload
python test_portfolio.py
```
