# Energy Investment Optimization API

## Overview

The optimization API helps users determine the optimal mix of renewable energy investments (Solar PV, Wind, Battery) to minimize their electricity costs based on their consumption profile.

## Endpoint

**POST /optimize**

Analyzes a user's consumption profile and recommends the optimal investment strategy.

## Request Body

```json
{
  "pod_id": "00011",
  "electricity_price": 0.30,
  "feed_in_tariff": 0.05,
  "budget": 10000,
  "max_shares_per_project": 100
}
```

### Parameters

- `pod_id` (required): Load curve identifier (e.g., "00011", "00012")
- `electricity_price` (optional): Cost of grid electricity in €/kWh (default: 0.30)
- `feed_in_tariff` (optional): Revenue from exported electricity in €/kWh (default: 0.05)
- `budget` (optional): Maximum investment budget in € (default: unlimited)
- `max_shares_per_project` (optional): Maximum shares per project (default: 100)

## Response

```json
{
  "recommendations": [
    {
      "project_id": "000003",
      "project_name": "Northern Wind Farm Expansion",
      "energy_type": "wind",
      "recommended_shares": 15,
      "investment_amount": 12750.00,
      "annual_benefit": 1850.50,
      "payback_years": 6.89,
      "capacity_kw": 22.5
    }
  ],
  "total_investment": 12750.00,
  "annual_savings": 1850.50,
  "payback_period_years": 6.89,
  "baseline_annual_cost": 5200.00,
  "new_annual_cost": 3349.50,
  "energy_metrics": {
    "total_consumption_kwh": 17500.00,
    "total_production_kwh": 13200.00,
    "self_consumed_kwh": 8900.00,
    "grid_import_kwh": 8600.00,
    "grid_export_kwh": 4300.00,
    "self_consumption_rate": 67.42,
    "autarky_rate": 50.86
  },
  "summary": {
    "total_shares": 15,
    "total_capacity_kw": 22.5,
    "projects_count": 1
  }
}
```

## How It Works

### 1. Data Collection
- Loads the user's yearly consumption profile (15-minute intervals)
- Loads available renewable energy projects with their production profiles
- Retrieves project pricing and capacity information

### 2. Optimization Algorithm
The system uses a **greedy optimization approach**:

1. **Calculate ROI for each project**: For each available project, calculate the return on investment based on:
   - Self-consumption (electricity you produce and use directly)
   - Grid export revenue (excess electricity sold back to grid)
   - Avoided grid import costs

2. **Rank projects by payback period**: Projects with shorter payback periods are prioritized

3. **Greedy allocation**: Starting with the best ROI project:
   - Determine optimal number of shares
   - Allocate shares up to budget limit
   - Update remaining consumption
   - Move to next best project

4. **Calculate final metrics**: Compute overall savings, autarky rate, and payback period

### 3. Key Metrics

- **Self-consumption rate**: % of produced energy that you consume directly
- **Autarky rate**: % of your consumption covered by your own production
- **Payback period**: Years until investment is recovered through savings
- **Annual savings**: Yearly cost reduction from grid electricity + export revenue

## Example Use Cases

### Case 1: Optimize with Budget Constraint
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "pod_id": "00011",
    "budget": 5000,
    "electricity_price": 0.32
  }'
```

### Case 2: Unlimited Budget Optimization
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "pod_id": "00012",
    "electricity_price": 0.28,
    "feed_in_tariff": 0.06
  }'
```

### Case 3: Conservative Investment
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "pod_id": "00011",
    "budget": 3000,
    "max_shares_per_project": 10
  }'
```

## Algorithm Choice: Why Not LLM?

### Mathematical Optimization (Current Approach) ✅
**Pros:**
- Deterministic and reproducible results
- Fast computation (< 1 second)
- Explainable recommendations
- Guaranteed to find good solutions
- No API costs

**Cons:**
- Less flexible reasoning
- Can't explain trade-offs in natural language

### LLM-Based Approach (Alternative)
**When to use:**
- Need natural language explanations
- Want to consider qualitative factors (location preferences, risk tolerance)
- Need to explain complex trade-offs to users

**Recommended LLMs:**
1. **Claude 3.5 Sonnet** (Anthropic)
   - Best for reasoning and analysis
   - Good at explaining trade-offs
   - API: ~$3 per million input tokens

2. **GPT-4** (OpenAI)
   - Strong analytical capabilities
   - Good structured output
   - API: ~$10 per million input tokens

3. **Local Models** (Ollama)
   - Llama 3.1 70B for complex reasoning
   - Free, runs locally
   - Slower but no API costs

## Hybrid Approach (Recommended for Production)

Combine both approaches:

1. **Use mathematical optimization** for the actual calculations
2. **Use LLM** to:
   - Explain recommendations in natural language
   - Answer user questions about trade-offs
   - Provide personalized advice based on user preferences
   - Generate reports and summaries

Example hybrid flow:
```
User Request → Math Optimization → Results → LLM Explanation → User
```

## Future Enhancements

1. **Battery Storage Optimization**: Add intelligent battery sizing
2. **Time-of-Use Pricing**: Consider variable electricity rates
3. **Seasonal Analysis**: Optimize for seasonal consumption patterns
4. **Risk Analysis**: Monte Carlo simulation for uncertainty
5. **Multi-year Projections**: Long-term financial modeling
6. **LLM Integration**: Natural language explanations and Q&A
