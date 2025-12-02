from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
import json
import csv
import logging

from api.config import DATA_FOLDER, PRODUCTION_FOLDER, PROJECTS_FOLDER
from api.services.optimization import optimize_investment

logger = logging.getLogger(__name__)
router = APIRouter()


class OptimizationRequest(BaseModel):
    """Request model for optimization endpoint"""
    pod_id: str  # Load curve identifier
    electricity_price: Optional[float] = 0.30  # €/kWh
    feed_in_tariff: Optional[float] = 0.05  # €/kWh
    budget: Optional[float] = None  # Maximum investment budget
    max_shares_per_project: Optional[int] = 100


@router.post("/optimize")
def optimize_energy_investment(request: OptimizationRequest) -> Dict:
    """
    Optimize renewable energy investment based on consumption profile.
    
    This endpoint analyzes a user's consumption profile and recommends
    the optimal mix of renewable energy projects (PV, Wind, Battery) to
    minimize electricity costs.
    
    Args:
        pod_id: Load curve identifier (e.g., "00011")
        electricity_price: Cost of grid electricity in €/kWh (default: 0.30)
        feed_in_tariff: Revenue from exported electricity in €/kWh (default: 0.05)
        budget: Optional maximum investment budget in € (default: unlimited)
        max_shares_per_project: Maximum shares per project (default: 100)
    
    Returns:
        Optimization results with investment recommendations
    """
    try:
        # Load consumption profile
        filename = f"LU_ENO_DELPHI_LU_virtual_ind_{request.pod_id}.csv"
        file_path = DATA_FOLDER / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Load curve not found for POD: {request.pod_id}"
            )
        
        consumption_profile = []
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip header
            
            for row in csv_reader:
                if len(row) >= 2:
                    try:
                        consumption_profile.append(float(row[1]))
                    except ValueError:
                        continue
        
        logger.info(f"Loaded {len(consumption_profile)} consumption data points")
        
        # Load available projects
        projects_file = PROJECTS_FOLDER / "list.json"
        if not projects_file.exists():
            raise HTTPException(status_code=404, detail="Projects list not found")
        
        with open(projects_file, 'r', encoding='utf-8') as f:
            projects_list = json.load(f)
        
        # Load production profiles for each project
        available_projects = []
        for project in projects_list:
            project_id = project['id']
            
            # Try to load production profile
            production_file = PRODUCTION_FOLDER / f"{project_id}.json"
            if production_file.exists():
                with open(production_file, 'r', encoding='utf-8') as f:
                    production_data = json.load(f)
                
                production_profile = [
                    float(item.get('value', 0)) for item in production_data
                ]
                
                # Handle length mismatch by truncating to shorter length
                if len(production_profile) != len(consumption_profile):
                    min_length = min(len(production_profile), len(consumption_profile))
                    logger.warning(
                        f"Project {project_id}: production length {len(production_profile)} "
                        f"!= consumption length {len(consumption_profile)}. "
                        f"Truncating to {min_length} points."
                    )
                    production_profile = production_profile[:min_length]
                
                # Add production profile to project
                # For battery, use capacity_per_share if available, otherwise use capacity
                capacity_per_share = project.get('capacity_per_share', {}).get('value')
                if capacity_per_share is None:
                    capacity_per_share = project.get('capacity', {}).get('value', 1.0)
                
                project_with_profile = {
                    'id': project_id,
                    'name': project.get('name', project_id),
                    'energy': project.get('energy', 'unknown'),
                    'production_profile': production_profile,
                    'capacity_per_share': capacity_per_share,
                    'price_per_share': project.get('shares', {}).get('price', 1000),
                    'available_shares': project.get('shares', {}).get('available', 0),
                    'is_battery': project.get('energy') == 'battery'
                }
                
                available_projects.append(project_with_profile)
                logger.info(
                    f"Loaded project {project_id} ({project.get('name')}): "
                    f"{len(production_profile)} data points, "
                    f"€{project.get('shares', {}).get('price', 0)}/share"
                )
            else:
                logger.warning(f"Production file not found for project {project_id}")
        
        logger.info(f"Total projects with production profiles: {len(available_projects)}")
        
        if not available_projects:
            raise HTTPException(
                status_code=404,
                detail="No projects with production profiles found"
            )
        
        # Run optimization
        result = optimize_investment(
            consumption_profile=consumption_profile,
            available_projects=available_projects,
            electricity_price=request.electricity_price,
            feed_in_tariff=request.feed_in_tariff,
            budget=request.budget,
            max_shares_per_project=request.max_shares_per_project
        )
        
        logger.info(
            f"Optimization complete: {len(result['recommendations'])} projects recommended"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during optimization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during optimization: {str(e)}"
        )
