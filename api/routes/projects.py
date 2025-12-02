from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging

from api.config import PROJECTS_FOLDER, PRODUCTION_FOLDER
from api.utils.aggregation import aggregate_by_month, aggregate_by_day

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/projects")
def get_projects() -> List[Dict]:
    """
    Fetch the list of projects from local data folder.
    Returns a JSON array with project information.
    """
    file_path = PROJECTS_FOLDER / "list.json"

    try:
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Projects list not found")

        # Read and parse JSON
        with open(file_path, "r", encoding="utf-8") as jsonfile:
            projects_data = json.load(jsonfile)

        logger.info(
            f"Successfully loaded projects list with {len(projects_data)} projects"
        )
        return projects_data

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error reading projects list: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error reading projects list: {str(e)}"
        )


@router.get("/projects/{project_id}/production/monthly")
def get_project_production_monthly(
    project_id: str, year: Optional[int] = None
) -> List[Dict]:
    """
    Fetch production data aggregated by month for a specific project.
    
    Args:
        project_id: Project identifier
        year: Optional year filter (e.g., 2023)
    
    Returns:
        Time series with monthly aggregations (timestamp, value in kWh)
    """
    filename = f"{project_id}.json"
    file_path = PRODUCTION_FOLDER / filename

    try:
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Production data not found for project: {project_id}",
            )

        # Read and parse JSON
        with open(file_path, "r", encoding="utf-8") as jsonfile:
            all_data = json.load(jsonfile)

        # Aggregate by month
        monthly_data = aggregate_by_month(all_data, year=year)

        logger.info(
            f"Successfully aggregated {len(all_data)} records into {len(monthly_data)} months"
        )

        return monthly_data

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error reading production data: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error reading production data: {str(e)}"
        )


@router.get("/projects/{project_id}/production/daily")
def get_project_production_daily(
    project_id: str, year: Optional[int] = None, month: Optional[int] = None
) -> List[Dict]:
    """
    Fetch production data aggregated by day for a specific project.
    
    Args:
        project_id: Project identifier
        year: Optional year filter (e.g., 2023)
        month: Optional month filter (1-12)
    
    Returns:
        Time series with daily aggregations (timestamp, value in kWh)
    """
    filename = f"{project_id}.json"
    file_path = PRODUCTION_FOLDER / filename

    try:
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Production data not found for project: {project_id}",
            )

        # Validate month parameter
        if month and (month < 1 or month > 12):
            raise HTTPException(
                status_code=400, detail="Month must be between 1 and 12"
            )

        # Read and parse JSON
        with open(file_path, "r", encoding="utf-8") as jsonfile:
            all_data = json.load(jsonfile)

        # Aggregate by day
        daily_data = aggregate_by_day(all_data, year=year, month=month)

        logger.info(
            f"Successfully aggregated {len(all_data)} records into {len(daily_data)} days"
        )

        return daily_data

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error reading production data: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error reading production data: {str(e)}"
        )


@router.get("/projects")
def get_projects() -> List[Dict]:
    """
    Fetch the list of projects from local data folder.
    Returns a JSON array with project information.
    """
    file_path = PROJECTS_FOLDER / "list.json"

    try:
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Projects list not found")

        # Read and parse JSON
        with open(file_path, "r", encoding="utf-8") as jsonfile:
            projects_data = json.load(jsonfile)

        logger.info(
            f"Successfully loaded projects list with {len(projects_data)} projects"
        )
        return projects_data

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error reading projects list: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error reading projects list: {str(e)}"
        )


@router.get("/projects/{project_id}/production")
def get_project_production(
    project_id: str,
    page: int = 1,
    page_size: int = 100,
    date: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> Dict:
    """
    Fetch production data for a specific project from local data folder.
    Returns paginated time series data with timestamp and value.

    Args:
        project_id: Project identifier
        page: Page number (default: 1)
        page_size: Number of records per page (default: 100)
        date: Specific date to query (format: YYYY-MM-DD)
        from_date: Start date for range query (format: YYYY-MM-DD)
        to_date: End date for range query (format: YYYY-MM-DD)

    Note: Use either 'date' for a single day or 'from_date'/'to_date' for a range.
    """
    filename = f"{project_id}.json"
    file_path = PRODUCTION_FOLDER / filename

    try:
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Production data not found for project: {project_id}",
            )

        # Validate pagination parameters
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if page_size < 1 or page_size > 1000:
            raise HTTPException(
                status_code=400, detail="Page size must be between 1 and 1000"
            )

        # Validate date parameters
        if date and (from_date or to_date):
            raise HTTPException(
                status_code=400,
                detail="Cannot use 'date' parameter with 'from_date' or 'to_date'",
            )

        # Parse date filters
        filter_start = None
        filter_end = None

        if date:
            try:
                filter_start = datetime.strptime(date, "%Y-%m-%d")
                filter_end = filter_start.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
                )
        elif from_date or to_date:
            try:
                if from_date:
                    filter_start = datetime.strptime(from_date, "%Y-%m-%d")
                if to_date:
                    filter_end = datetime.strptime(to_date, "%Y-%m-%d").replace(
                        hour=23, minute=59, second=59
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
                )

        # Read and parse JSON
        with open(file_path, "r", encoding="utf-8") as jsonfile:
            all_data = json.load(jsonfile)

        # Filter by date if specified
        time_series = []
        for item in all_data:
            timestamp_str = item.get("timestamp", "")

            # Apply date filter if specified
            if filter_start or filter_end:
                try:
                    # Parse timestamp (ISO format)
                    if "T" in timestamp_str:
                        row_date = datetime.fromisoformat(
                            timestamp_str.replace("Z", "")
                        )
                    else:
                        row_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                    # Check if within date range
                    if filter_start and row_date < filter_start:
                        continue
                    if filter_end and row_date > filter_end:
                        continue
                except ValueError:
                    # Skip items with invalid timestamps
                    continue

            time_series.append({"timestamp": timestamp_str, "value": item.get("value")})

        total_records = len(time_series)

        if total_records == 0 and (date or from_date or to_date):
            logger.warning(f"No data found for the specified date range")

        total_pages = (
            (total_records + page_size - 1) // page_size if total_records > 0 else 1
        )

        # Calculate pagination slice
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        # Get paginated data
        paginated_data = time_series[start_idx:end_idx]

        logger.info(
            f"Successfully loaded page {page}/{total_pages} with {len(paginated_data)} records"
            + (f" (filtered by date)" if (date or from_date or to_date) else "")
        )

        return {
            "data": paginated_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
        }

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error reading production data: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error reading production data: {str(e)}"
        )
