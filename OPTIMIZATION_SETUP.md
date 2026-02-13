# Optimization API Setup Complete

## What Was Created

### 1. Production Data Files (2023-2024)
- **00001.json**: Battery storage (70,176 data points, all zeros)
- **00002.json**: Wind farm production (70,176 data points, 1.5 kW capacity)
- **00003.json**: Solar PV production (70,176 data points, 2.5 kWc capacity)

### 2. API Endpoints
- **POST /optimize**: Investment optimization endpoint

### 3. Files Structure
```
api/
├── services/
│   └── optimization.py      # Core optimization logic
└── routes/
    └── optimization.py       # API endpoint

data/
└── projects/
    ├── list.json            # Project definitions with pricing
    └── production/
        ├── 00001.json       # Battery (0 kW production)
        ├── 00002.json       # Wind (1.5 kW per share)
        └── 00003.json       # Solar (2.5 kWc per share)

docs/
└── OPTIMIZATION_API.md      # Complete API documentation
```

## How to Test

### 1. Start the Server
```bash
python -m uvicorn main:app --reload --port 8000
```

### 2. Test the Optimization
```bash
python test_optimization.py
```

Or use curl:
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "pod_id": "000011",
    "electricity_price": 0.30,
    "feed_in_tariff": 0.05,
    "budget": 10000,
    "max_shares_per_project": 50
  }'
```

## Sample Request

```json
{
  "pod_id": "000011",
  "electricity_price": 0.30,
  "feed_in_tariff": 0.05,
  "budget": 10000,
  "max_shares_per_project": 50
}
```

## Expected Response

```json
{
  "recommendations": [
    {
      "project_id": "00002",
      "project_name": "Northern Wind Farm Expansion",
      "energy_type": "wind",
      "recommended_shares": 11,
      "investment_amount": 9350.00,
      "annual_benefit": 2450.75,
      "payback_years": 3.81,
      "capacity_kw": 16.5
    }
  ],
  "total_investment": 9350.00,
  "annual_savings": 2450.75,
  "payback_period_years": 3.81,
  "baseline_annual_cost": 17936.30,
  "new_annual_cost": 15485.55,
  "energy_metrics": {
    "total_consumption_kwh": 59787.67,
    "total_production_kwh": 26492.44,
    "self_consumed_kwh": 18500.00,
    "grid_import_kwh": 41287.67,
    "grid_export_kwh": 7992.44,
    "self_consumption_rate": 69.83,
    "autarky_rate": 30.95
  },
  "summary": {
    "total_shares": 11,
    "total_capacity_kw": 16.5,
    "projects_count": 1
  }
}
```

## Project Details

### Available Projects

1. **Battery Storage (00001)**
   - Price: €750/share
   - Capacity: 5 kWh per share
   - Type: Energy storage
   - Note: Currently has 0 production (storage only)

2. **Solar PV (00002)**  
   - Price: €1,250/share
   - Capacity: 1200 kWc total
   - Type: Solar photovoltaic
   - Production: Realistic weather patterns

3. **Wind Farm (00003)**
   - Price: €850/share
   - Capacity: 1.5 kW per share
   - Type: Wind turbine
   - Production: Stable, consistent output

## How the Algorithm Works

1. **Load Data**: Consumption profile + project production profiles
2. **Calculate ROI**: For each project, calculate self-consumption benefit
3. **Rank Projects**: Sort by payback period (best ROI first)
4. **Greedy Allocation**: Allocate shares to best projects within budget
5. **Return Results**: Investment recommendations + financial projections

## Key Metrics Explained

- **Self-consumption rate**: % of produced energy consumed directly (higher is better)
- **Autarky rate**: % of consumption covered by own production (energy independence)
- **Payback period**: Years to recover investment through savings
- **Annual savings**: Yearly reduction in electricity costs

## Why Not Use LLM?

The current implementation uses **mathematical optimization** instead of LLM because:

✅ **Deterministic**: Same input always gives same output
✅ **Fast**: < 1 second response time
✅ **Accurate**: Guaranteed good solutions
✅ **Explainable**: Clear calculation logic
✅ **Free**: No API costs

### When to Add LLM (Future Enhancement)

Use LLM for:
- Natural language explanations of recommendations
- Answering user questions about trade-offs
- Personalized advice based on preferences
- Generating investment reports

**Recommended LLMs:**
- Claude 3.5 Sonnet (best for reasoning)
- GPT-4 (strong analytics)
- Llama 3.1 70B (free, local)

## Troubleshooting

### No Recommendations Returned
- Check that production files exist and match project IDs
- Verify consumption profile exists for the POD ID
- Check logs for data length mismatches

### Length Mismatch Warnings
- Production data: 70,176 points (2023-2024 with leap year)
- Some consumption files may have fewer points
- Algorithm automatically truncates to shorter length

### Battery Shows No Benefit
- Battery currently has 0 production values
- Battery optimization requires special handling (future enhancement)
- Focus on Solar and Wind for now

## Next Steps

1. **Test the API** with different POD IDs and budgets
2. **Add battery logic** for intelligent storage optimization
3. **Integrate LLM** for natural language explanations
4. **Add time-of-use pricing** for more accurate calculations
5. **Create frontend** to visualize recommendations
