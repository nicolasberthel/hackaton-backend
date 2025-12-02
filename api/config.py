from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FOLDER = BASE_DIR / "data" / "profiles"
MIX_FOLDER = BASE_DIR / "data" / "mix"
PROJECTS_FOLDER = BASE_DIR / "data" / "projects"
PRODUCTION_FOLDER = BASE_DIR / "data" / "projects" / "production"

logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"DATA_FOLDER: {DATA_FOLDER}")
logger.info(f"MIX_FOLDER: {MIX_FOLDER}")
logger.info(f"PROJECTS_FOLDER: {PROJECTS_FOLDER}")
logger.info(f"PRODUCTION_FOLDER: {PRODUCTION_FOLDER}")
