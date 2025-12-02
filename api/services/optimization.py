"""
Energy investment optimization service.
Determines optimal mix of PV, Wind, and Battery investments to minimize costs.
"""

from typing import List, Dict, Optional
import numpy as np
from datetime import datetime
from scipy.optimize import linprog


def calculate_self_consumption_rate(
    consumption: List[float],
    production: List[float],
    battery_capacity_kwh: float = 0
) -> Dict:
    """
    Calculate self-consumption rate with optional battery storage.
    
    Args:
        consumption: Hourly consumption in kW
        production: Hourly production in kW
        battery_capacity_kwh: Battery capacity in kWh
    
    Returns:
        Dict with self-consumption metrics
    """
    total_consumption = sum(consumption)
    total_production = sum(production)
    
    # Simple battery simulation
    battery_level = 0
    grid_import = 0
    grid_export = 0
    self_consumed = 0
    
    for cons, prod in zip(consumption, production):
        net = prod - cons  # Positive = surplus, Negative = deficit
        
        if net >= 0:  # Surplus production
            # First, consume directly
            self_consumed += cons
            
            # Then charge battery
            if battery_capacity_kwh > 0:
                charge_amount = min(net, battery_capacity_kwh - battery_level)
                battery_level += charge_amount
                net -= charge_amount
            
            # Export remaining
            grid_export += net
        else:  # Deficit (need more energy)
            # First, use production directly
            self_consumed += prod
            deficit = abs(net)
            
            # Then discharge battery
            if battery_capacity_kwh > 0 and battery_level > 0:
                discharge_amount = min(deficit, battery_level)
                battery_level -= discharge_amount
                deficit -= discharge_amount
            
            # Import remaining from grid
            grid_import += deficit
    
    self_consumption_rate = (self_consumed / total_production * 100) if total_production > 0 else 0
    autarky_rate = (self_consumed / total_consumption * 100) if total_consumption > 0 else 0
    
    return {
        'total_consumption_kwh': total_consumption * 0.25,  # 15-min intervals
        'total_production_kwh': total_production * 0.25,
        'self_consumed_kwh': self_consumed * 0.25,
        'grid_import_kwh': grid_import * 0.25,
        'grid_export_kwh': grid_export * 0.25,
        'self_consumption_rate': round(self_consumption_rate, 2),
        'autarky_rate': round(autarky_rate, 2)
    }


def optimize_investment(
    consumption_profile: List[float],
    available_projects: List[Dict],
    electricity_price: float = 0.30,  # €/kWh
    feed_in_tariff: float = 0.05,  # €/kWh
    budget: Optional[float] = None,
    max_shares_per_project: int = 100
) -> Dict:
    """
    Optimize investment in renewable energy projects.
    
    Args:
        consumption_profile: List of consumption values (kW) for each 15-min interval
        available_projects: List of project dicts with production profiles
        electricity_price: Cost of grid electricity (€/kWh)
        feed_in_tariff: Revenue from exported electricity (€/kWh)
        budget: Optional maximum investment budget (€)
        max_shares_per_project: Maximum shares per project
    
    Returns:
        Optimization results with recommended investments
    """
    
    # Prepare data
    n_intervals = len(consumption_profile)
    n_projects = len(available_projects)
    
    # Calculate baseline cost (no investment)
    baseline_consumption_kwh = sum(consumption_profile) * 0.25
    baseline_cost = baseline_consumption_kwh * electricity_price
    
    # Simple greedy optimization approach
    # For each project, calculate ROI and self-consumption benefit
    project_scores = []
    
    for project in available_projects:
        project_id = project.get('id', 'unknown')
        capacity = project.get('capacity_per_share', 1.0)
        price_per_share = project.get('price_per_share', 1000)
        energy_type = project.get('energy', 'solar')
        production_profile = project.get('production_profile', [])
        is_battery = project.get('is_battery', False)
        
        # Ensure production profile matches consumption length
        if len(production_profile) != n_intervals:
            # Skip or pad/truncate
            continue
        
        # For battery, calculate benefit differently
        if is_battery:
            # Battery stores excess production and releases during high consumption
            # Estimate benefit: battery enables better use of renewable energy
            # Simplified: assume battery can shift ~30% of excess production to peak times
            
            # Calculate potential benefit with battery storage
            battery_capacity = capacity  # kWh per share
            
            # Estimate: battery can save money by storing cheap/excess energy
            # and using it during expensive times
            # Simplified calculation: assume 1 cycle per day, 80% efficiency
            daily_cycles = 1
            efficiency = 0.8
            annual_cycles = daily_cycles * 365
            
            # Energy that can be shifted per year
            energy_shifted_kwh = battery_capacity * annual_cycles * efficiency
            
            # Benefit: avoid buying at peak price (simplified)
            # Assume 50% of shifted energy would have been bought at grid price
            annual_benefit = energy_shifted_kwh * 0.5 * electricity_price
            
            metrics = {
                'self_consumption_rate': 0,
                'autarky_rate': 0
            }
        else:
            # Calculate benefit of 1 share for production projects
            metrics = calculate_self_consumption_rate(
                consumption_profile,
                production_profile,
                battery_capacity_kwh=0
            )
            
            # Annual savings
            grid_savings = metrics['self_consumed_kwh'] * electricity_price
            export_revenue = metrics['grid_export_kwh'] * feed_in_tariff
            annual_benefit = grid_savings + export_revenue
        
        # Simple ROI (payback period in years)
        payback_years = price_per_share / annual_benefit if annual_benefit > 0 else 999
        
        project_scores.append({
            'project_id': project_id,
            'project_name': project.get('name', project_id),
            'energy_type': energy_type,
            'capacity_per_share': capacity,
            'price_per_share': price_per_share,
            'annual_benefit': annual_benefit,
            'payback_years': payback_years,
            'self_consumption_rate': metrics.get('self_consumption_rate', 0),
            'autarky_rate': metrics.get('autarky_rate', 0),
            'production_profile': production_profile,
            'is_battery': is_battery
        })
    
    # Sort by payback period (best ROI first)
    project_scores.sort(key=lambda x: x['payback_years'])
    
    # Greedy allocation
    recommendations = []
    total_investment = 0
    remaining_consumption = consumption_profile.copy()
    
    for project in project_scores:
        if budget and total_investment >= budget:
            break
        
        # Determine optimal number of shares
        best_shares = 0
        best_benefit = 0
        
        # For battery, use simpler calculation
        if project.get('is_battery', False):
            for shares in range(1, max_shares_per_project + 1):
                investment = shares * project['price_per_share']
                
                if budget and (total_investment + investment) > budget:
                    break
                
                # Battery benefit scales linearly with capacity
                battery_capacity = project['capacity_per_share'] * shares
                
                # Simplified: 1 cycle per day, 80% efficiency
                daily_cycles = 1
                efficiency = 0.8
                annual_cycles = daily_cycles * 365
                energy_shifted_kwh = battery_capacity * annual_cycles * efficiency
                annual_benefit = energy_shifted_kwh * 0.5 * electricity_price
                
                if annual_benefit > best_benefit:
                    best_benefit = annual_benefit
                    best_shares = shares
        else:
            # For production projects
            for shares in range(1, max_shares_per_project + 1):
                investment = shares * project['price_per_share']
                
                if budget and (total_investment + investment) > budget:
                    break
                
                # Scale production by number of shares
                scaled_production = [p * shares for p in project['production_profile']]
                
                metrics = calculate_self_consumption_rate(
                    remaining_consumption,
                    scaled_production,
                    battery_capacity_kwh=0
                )
                
                grid_savings = metrics['self_consumed_kwh'] * electricity_price
                export_revenue = metrics['grid_export_kwh'] * feed_in_tariff
                annual_benefit = grid_savings + export_revenue
                
                if annual_benefit > best_benefit:
                    best_benefit = annual_benefit
                    best_shares = shares
        
        if best_shares > 0:
            investment = best_shares * project['price_per_share']
            
            if not project.get('is_battery', False):
                scaled_production = [p * best_shares for p in project['production_profile']]
                
                # Update remaining consumption
                for i in range(len(remaining_consumption)):
                    remaining_consumption[i] = max(0, remaining_consumption[i] - scaled_production[i])
            
            capacity_unit = 'kWh' if project.get('is_battery', False) else 'kW'
            
            recommendations.append({
                'project_id': project['project_id'],
                'project_name': project['project_name'],
                'energy_type': project['energy_type'],
                'recommended_shares': best_shares,
                'investment_amount': investment,
                'annual_benefit': best_benefit,
                'payback_years': investment / best_benefit if best_benefit > 0 else 999,
                'capacity': project['capacity_per_share'] * best_shares,
                'capacity_unit': capacity_unit
            })
            
            total_investment += investment
    
    # Calculate final metrics
    total_production = [0] * n_intervals
    for rec in recommendations:
        project = next(p for p in project_scores if p['project_id'] == rec['project_id'])
        scaled_prod = [p * rec['recommended_shares'] for p in project['production_profile']]
        total_production = [total_production[i] + scaled_prod[i] for i in range(n_intervals)]
    
    final_metrics = calculate_self_consumption_rate(
        consumption_profile,
        total_production,
        battery_capacity_kwh=0
    )
    
    # Calculate financial summary
    annual_grid_cost = final_metrics['grid_import_kwh'] * electricity_price
    annual_export_revenue = final_metrics['grid_export_kwh'] * feed_in_tariff
    annual_savings = baseline_cost - annual_grid_cost + annual_export_revenue
    
    return {
        'recommendations': recommendations,
        'total_investment': round(total_investment, 2),
        'annual_savings': round(annual_savings, 2),
        'payback_period_years': round(total_investment / annual_savings, 2) if annual_savings > 0 else None,
        'baseline_annual_cost': round(baseline_cost, 2),
        'new_annual_cost': round(annual_grid_cost - annual_export_revenue, 2),
        'energy_metrics': final_metrics,
        'summary': {
            'total_shares': sum(r['recommended_shares'] for r in recommendations),
            'projects_count': len(recommendations),
            'by_type': {
                rec['energy_type']: {
                    'shares': rec['recommended_shares'],
                    'capacity': rec['capacity'],
                    'unit': rec['capacity_unit']
                }
                for rec in recommendations
            }
        }
    }
