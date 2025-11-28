from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "data" / "profiles"
MIX_FOLDER = BASE_DIR / "data" / "mix"

logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"DATA_FOLDER: {DATA_FOLDER}")
logger.info(f"MIX_FOLDER: {MIX_FOLDER}")


@app.get("/status")
def get_status():
    return "OK"

@app.get("/loadcurve/{pod}")
def get_loadcurve(pod: str, page: int = 1, page_size: int = 100) -> Dict:
    """
    Fetch load curve data for a specific POD from local data folder.
    Returns paginated time series data with timestamp and value.
    
    Args:
        pod: POD identifier
        page: Page number (default: 1)
        page_size: Number of records per page (default: 100)
    """
    filename = f"LU_ENO_DELPHI_LU_virtual_ind_{pod}.csv"
    file_path = DATA_FOLDER / filename
    
    try:
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Load curve not found for POD: {pod}")
        
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if page_size < 1 or page_size > 1000:
            raise HTTPException(status_code=400, detail="Page size must be between 1 and 1000")
        
        # Read and parse CSV
        time_series = []
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip header row
            
            # Build time series array
            for row in csv_reader:
                if len(row) >= 2:
                    time_series.append({
                        "timestamp": row[0],
                        "value": row[1]
                    })
        
        total_records = len(time_series)
        total_pages = (total_records + page_size - 1) // page_size
        
        # Calculate pagination slice
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Get paginated data
        paginated_data = time_series[start_idx:end_idx]
        
        logger.info(f"Successfully loaded page {page}/{total_pages} with {len(paginated_data)} records")
        
        return {
            "data": paginated_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading load curve: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading load curve: {str(e)}")


@app.get("/mix/{type}")
def get_mix(type: str) -> List[Dict[str, float]]:
    """
    Fetch energy mix data for a specific type from local data folder.
    Returns a JSON array with hourly solar, wind, battery, and consumption data.
    """
    filename = f"{type}.json"
    file_path = MIX_FOLDER / filename
    
    try:
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Mix data not found for type: {type}")
        
        # Read and parse JSON
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            mix_data = json.load(jsonfile)
        
        logger.info(f"Successfully loaded mix data with {len(mix_data)} records")
        return mix_data
        
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        logger.error(f"Error reading mix data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading mix data: {str(e)}")
