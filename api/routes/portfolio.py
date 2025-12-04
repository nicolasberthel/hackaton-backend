from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

from api.config import PROJECTS_FOLDER, PRODUCTION_FOLDER, DATA_FOLDER

logger = logging.getLogger(__name__)
router = APIRouter()


def load_user_portfolio(user_id: str) -> Optional[Dict]:
    """Load user portfolio from storage."""
    portfolios_file = Path("data/users/portfolios.json")
    
    if not portfolios_file.exists():
        return None
    
    with open(portfolios_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for user in data.get('users', []):
        if user['user_id'] == user_id:
            return user
    
    return None


def calculate_production_for_period(
    project_id: str,
    shares: int,
    start_date: str,
    end_date: Optional[str] = None
) -> Dict:
    """Calculate production for a specific period."""
    production_file = PRODUCTION_FOLDER / f"{project_id}.json"
    
    if not production_file.exists():
        return {
            'total_kwh': 0,
            'data_points': 0,
            'error': 'Production data not found'
        }
    
    with open(production_file, 'r', encoding='utf-8') as f:
        production_data = json.load(f)
    
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date) if end_date else datetime.now()
    
    total_production = 0
    count = 0
    
    for item in production_data:
        timestamp_str = item.get('timestamp', '')
        value = float(item.get('value', 0))
        
        try:
            if 'T' in timestamp_str:
                item_dt = datetime.fromisoformat(timestamp_str.replace('Z', ''))
            else:
                item_dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            if start_dt <= item_dt <= end_dt:
                total_production += value
                count += 1
        except ValueError:
            continue
    
    # Convert to kWh (15-minute intervals)
    total_kwh = total_production * 0.25
    
    return {
        'total_kwh': round(total_kwh * shares, 2),
        'data_points': count,
        'start_date': start_date,
        'end_date': end_date or datetime.now().isoformat()
    }


@router.get("/portfolio/{user_id}")
def get_user_portfolio(
    user_id: str,
    include_production: bool = True,
    period: Optional[str] = "ytd"  # ytd, 1m, 3m, 6m, 1y, all
) -> Dict:
    """
    Get user's investment portfolio with performance metrics.
    
    Args:
        user_id: User identifier
        include_production: Include production data (default: True)
        period: Time period for production calculation (ytd, 1m, 3m, 6m, 1y, all)
    
    Returns:
        Portfolio details with investments, production, and performance
    """
    try:
        # Load user portfolio
        user_data = load_user_portfolio(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail=f"Portfolio not found for user: {user_id}"
            )
        
        # Calculate period dates
        end_date = datetime.now()
        
        if period == "1m":
            start_date = end_date - timedelta(days=30)
        elif period == "3m":
            start_date = end_date - timedelta(days=90)
        elif period == "6m":
            start_date = end_date - timedelta(days=180)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "ytd":
            start_date = datetime(end_date.year, 1, 1)
        else:  # all
            start_date = datetime(2023, 1, 1)
        
        # Group transactions by project_id and calculate positions
        from collections import defaultdict
        grouped_investments = defaultdict(lambda: {
            'shares': 0,
            'total_cost': 0,
            'transactions': []
        })
        
        for transaction in user_data.get('transactions', []):
            project_id = transaction['project_id']
            direction = transaction.get('direction', 'buy')
            shares = transaction['shares']
            price_per_share = transaction['purchase_price_per_share']
            
            # Store project metadata
            grouped_investments[project_id]['project_name'] = transaction['project_name']
            grouped_investments[project_id]['energy_type'] = transaction['energy_type']
            grouped_investments[project_id]['capacity_per_share'] = transaction['capacity_per_share']
            grouped_investments[project_id]['capacity_unit'] = transaction['capacity_unit']
            grouped_investments[project_id]['current_value_per_share'] = transaction['current_value_per_share']
            
            # Calculate position based on direction
            if direction == 'buy':
                grouped_investments[project_id]['shares'] += shares
                grouped_investments[project_id]['total_cost'] += shares * price_per_share
            elif direction == 'sell':
                # For sell, reduce shares and proportionally reduce cost basis
                if grouped_investments[project_id]['shares'] > 0:
                    avg_cost = grouped_investments[project_id]['total_cost'] / grouped_investments[project_id]['shares']
                    grouped_investments[project_id]['shares'] -= shares
                    grouped_investments[project_id]['total_cost'] -= shares * avg_cost
            
            # Store transaction history
            grouped_investments[project_id]['transactions'].append({
                'date': transaction['purchase_date'],
                'direction': direction,
                'shares': shares,
                'price_per_share': price_per_share
            })
        
        # Process grouped investments
        investments_detail = []
        total_investment = 0
        total_current_value = 0
        total_production_kwh = 0
        
        by_energy_type = {
            'solar': {'shares': 0, 'investment': 0, 'capacity': 0, 'production': 0},
            'wind': {'shares': 0, 'investment': 0, 'capacity': 0, 'production': 0},
            'battery': {'shares': 0, 'investment': 0, 'capacity': 0, 'production': 0}
        }
        
        for project_id, project_data in grouped_investments.items():
            shares = project_data['shares']
            total_cost = project_data['total_cost']
            current_price = project_data['current_value_per_share']
            energy_type = project_data['energy_type']
            
            # Skip if no shares remaining (fully sold)
            if shares <= 0:
                continue
            
            current_value = shares * current_price
            gain_loss = current_value - total_cost
            gain_loss_pct = (gain_loss / total_cost * 100) if total_cost > 0 else 0
            
            # Average purchase price (cost basis)
            avg_purchase_price = total_cost / shares if shares > 0 else 0
            
            total_investment += total_cost
            total_current_value += current_value
            
            # Calculate production if requested
            production_data = None
            if include_production and energy_type != 'battery':
                production_data = calculate_production_for_period(
                    project_id,
                    shares,
                    start_date.isoformat(),
                    end_date.isoformat()
                )
                total_production_kwh += production_data['total_kwh']
            
            # Calculate days held (from first buy transaction)
            buy_transactions = [t for t in project_data['transactions'] if t['direction'] == 'buy']
            if buy_transactions:
                first_purchase = min(buy_transactions, key=lambda x: x['date'])
                purchase_dt = datetime.fromisoformat(first_purchase['date'])
                days_held = (end_date - purchase_dt).days
            else:
                days_held = 0
            
            # Annualized return
            if days_held > 0:
                annualized_return = (gain_loss_pct / days_held * 365)
            else:
                annualized_return = 0
            
            investment_detail = {
                'project_id': project_id,
                'project_name': project_data['project_name'],
                'energy_type': energy_type,
                'shares': shares,
                'capacity': shares * project_data['capacity_per_share'],
                'capacity_unit': project_data['capacity_unit'],
                'first_purchase_date': first_purchase['date'] if buy_transactions else None,
                'days_held': days_held,
                'transaction_history': sorted(project_data['transactions'], key=lambda x: x['date']),
                'investment': {
                    'average_purchase_price': round(avg_purchase_price, 2),
                    'total_cost_basis': round(total_cost, 2),
                    'current_price_per_share': current_price,
                    'current_value': round(current_value, 2),
                    'gain_loss': round(gain_loss, 2),
                    'gain_loss_percentage': round(gain_loss_pct, 2),
                    'annualized_return': round(annualized_return, 2)
                }
            }
            
            if production_data:
                investment_detail['production'] = production_data
            
            investments_detail.append(investment_detail)
            
            # Aggregate by type
            by_energy_type[energy_type]['shares'] += shares
            by_energy_type[energy_type]['investment'] += total_cost
            by_energy_type[energy_type]['capacity'] += shares * project_data['capacity_per_share']
            if production_data:
                by_energy_type[energy_type]['production'] += production_data['total_kwh']
        
        # Calculate overall performance
        total_gain_loss = total_current_value - total_investment
        total_gain_loss_pct = (total_gain_loss / total_investment * 100) if total_investment > 0 else 0
        
        # Estimate annual savings (simplified)
        electricity_price = 0.30  # €/kWh
        feed_in_tariff = 0.05  # €/kWh
        
        # Assume 50% self-consumption, 50% export
        annual_production_estimate = total_production_kwh * (365 / max((end_date - start_date).days, 1))
        self_consumed = annual_production_estimate * 0.5
        exported = annual_production_estimate * 0.5
        
        estimated_annual_savings = (self_consumed * electricity_price) + (exported * feed_in_tariff)
        
        # Payback calculation
        if estimated_annual_savings > 0:
            payback_years = total_investment / estimated_annual_savings
        else:
            payback_years = None
        
        # Load user's consumption data
        consumption_data = None
        pod_id = user_data.get('pod_id')
        if pod_id:
            try:
                from api.config import DATA_FOLDER
                import csv
                
                filename = f"LU_ENO_DELPHI_LU_virtual_ind_{pod_id}.csv"
                file_path = DATA_FOLDER / filename
                
                if file_path.exists():
                    consumption_profile = []
                    with open(file_path, 'r', encoding='utf-8') as csvfile:
                        csv_reader = csv.reader(csvfile)
                        next(csv_reader)  # Skip header
                        
                        for row in csv_reader:
                            if len(row) >= 2:
                                timestamp_str = row[0]
                                value = float(row[1])
                                
                                try:
                                    if 'T' in timestamp_str:
                                        item_dt = datetime.fromisoformat(timestamp_str.replace('Z', ''))
                                    else:
                                        item_dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                    
                                    if start_date <= item_dt <= end_date:
                                        consumption_profile.append(value)
                                except ValueError:
                                    continue
                    
                    if consumption_profile:
                        total_consumption_kwh = sum(consumption_profile) * 0.25
                        avg_consumption_kw = sum(consumption_profile) / len(consumption_profile)
                        max_consumption_kw = max(consumption_profile)
                        
                        # Calculate self-consumption rate
                        if total_production_kwh > 0 and total_consumption_kwh > 0:
                            # Simplified: assume 50% of production is self-consumed
                            self_consumed_kwh = min(total_production_kwh * 0.5, total_consumption_kwh)
                            self_consumption_rate = (self_consumed_kwh / total_production_kwh * 100)
                            autarky_rate = (self_consumed_kwh / total_consumption_kwh * 100)
                        else:
                            self_consumption_rate = 0
                            autarky_rate = 0
                        
                        consumption_data = {
                            'total_kwh': round(total_consumption_kwh, 2),
                            'average_kw': round(avg_consumption_kw, 4),
                            'max_kw': round(max_consumption_kw, 4),
                            'data_points': len(consumption_profile),
                            'self_consumption_rate': round(self_consumption_rate, 2),
                            'autarky_rate': round(autarky_rate, 2)
                        }
            except Exception as e:
                logger.warning(f"Could not load consumption data: {str(e)}")
        
        return {
            'user_id': user_id,
            'user_name': user_data.get('name'),
            'pod_id': user_data.get('pod_id'),
            'registration_date': user_data.get('registration_date'),
            'period': {
                'type': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days
            },
            'summary': {
                'total_projects': len(investments_detail),
                'total_shares': sum(t['shares'] for t in user_data['transactions'] if t.get('direction') == 'buy'),
                'total_investment': round(total_investment, 2),
                'current_value': round(total_current_value, 2),
                'total_gain_loss': round(total_gain_loss, 2),
                'total_gain_loss_percentage': round(total_gain_loss_pct, 2),
                'total_production_kwh': round(total_production_kwh, 2),
                'estimated_annual_savings': round(estimated_annual_savings, 2),
                'payback_years': round(payback_years, 2) if payback_years else None
            },
            'by_energy_type': {
                energy_type: {
                    'shares': data['shares'],
                    'investment': round(data['investment'], 2),
                    'capacity': round(data['capacity'], 2),
                    'production_kwh': round(data['production'], 2)
                }
                for energy_type, data in by_energy_type.items()
                if data['shares'] > 0
            },
            'investments': investments_detail,
            'consumption': consumption_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving portfolio: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving portfolio: {str(e)}"
        )


@router.get("/portfolio/{user_id}/production")
def get_portfolio_production(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    aggregation: Optional[str] = "daily"  # hourly, daily, monthly
) -> Dict:
    """
    Get detailed production data for user's portfolio.
    
    Args:
        user_id: User identifier
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        aggregation: Time aggregation (hourly, daily, monthly)
    
    Returns:
        Detailed production time series
    """
    try:
        user_data = load_user_portfolio(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail=f"Portfolio not found for user: {user_id}"
            )
        
        # TODO: Implement detailed production aggregation
        # This would aggregate production data across all projects
        
        return {
            'user_id': user_id,
            'message': 'Detailed production endpoint - to be implemented',
            'transactions_count': len(user_data.get('transactions', []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving production data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving production data: {str(e)}"
        )
