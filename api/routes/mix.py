from fastapi import APIRouter, HTTPException
from typing import List, Dict
import json
import logging

from api.config import MIX_FOLDER

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/mix/{type}")
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
            raise HTTPException(
                status_code=404, detail=f"Mix data not found for type: {type}"
            )

        # Read and parse JSON
        with open(file_path, "r", encoding="utf-8") as jsonfile:
            mix_data = json.load(jsonfile)

        logger.info(f"Successfully loaded mix data with {len(mix_data)} records")
        return mix_data

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error reading mix data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading mix data: {str(e)}")
