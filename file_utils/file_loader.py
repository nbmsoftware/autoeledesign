import ezdxf
from ezdxf.addons import odafc
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_cad_file(file_path: str, audit: bool = False, odafc_version: str = None):
    """
    Load a CAD file (DXF or DWG) and return an ezdxf.DXFDocument object.

    :param file_path: Path to the file (.dxf or .dwg)
    :param audit: Whether to audit/recover drawings (DWG only)
    :param odafc_version: Optional target version for DWG → DXF conversion
    :return: ezdxf.DXFDocument
    """
    file_path = Path(file_path)
    logger.debug(f"Attempting to load CAD file: {file_path}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = file_path.suffix.lower()

    try:
        if suffix == ".dxf":
            logger.info(f"Loading DXF file: {file_path}")
            doc = ezdxf.readfile(str(file_path))
        elif suffix == ".dwg":
            logger.info(f"Loading DWG file via ODAFC: {file_path}")
            doc = odafc.readfile(str(file_path), audit=audit, version=odafc_version)
        else:
            logger.error(f"Unsupported file type: {suffix}")
            raise ValueError(f"Unsupported file type: {suffix}. Only .dxf and .dwg are supported.")
    except Exception as e:
        logger.exception(f"Failed to load CAD file: {file_path}")
        raise RuntimeError(f"Failed to load CAD file: {file_path}") from e

    logger.info(f"Successfully loaded CAD file: {file_path}")
    return doc


def load_json_file(file_path: str):
    """
    Load and return JSON data from a file.

    :param file_path: Path to the JSON file.
    :return: The data loaded from the JSON file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
        raise e
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON in file: {file_path}")
        raise e