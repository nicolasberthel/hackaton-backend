import requests
import json

# Test the portfolio endpoint
base_url = "http://localhost:8000"

users = ["user_001", "user_002", "user_003"]

print("Testing Portfolio API...\n")
print("=" * 70)

for user_id in users:
    print(f"\n📊 Testing portfolio for {user_id}...")
    
    url = f"{base_url}/portfolio/{user_id}?period=ytd"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ {result['user_name']}")
            print(f"   POD: {result['pod_id']}")
            print(f"   Registration: {result['registration_date']}")
            
            summary = result['summary']
            print(f"\n   💰 Financial Summary:")
            print(f"      Total Investment: €{summary['total_investment']:,.2f}")
            print(f"      Current Value: €{summary['current_value']:,.2f}")
            print(f"      Gain/Loss: €{summary['total_gain_loss']:,.2f} ({summary['total_gain_loss_percentage']:.2f}%)")
            
            print(f"\n   ⚡ Energy Summary:")
            print(f"      Projects: {summary['total_projects']}")
            print(f"      Total Shares: {summary['total_shares']}")
            print(f"      Production (YTD): {summary['total_production_kwh']:,.2f} kWh")
            print(f"      Est. Annual Savings: €{summary['estimated_annual_savings']:,.2f}")
            
            if summary['payback_years']:
                print(f"      Payback Period: {summary['payback_years']:.1f} years")
            
            print(f"\n   📈 By Energy Type:")
            for energy_type, data in result['by_energy_type'].items():
                print(f"      {energy_type.capitalize()}: {data['shares']} shares, €{data['investment']:,.2f}, {data['production_kwh']:,.0f} kWh")
            
        else:
            print(f"   ❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("\n✨ Test complete!")
print("\nTo run the server:")
print("  python -m uvicorn main:app --reload")
