from ezdxf.addons import odafc
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def convert_dxf_dwg(source: str, dest: str= '',
                    version: str = 'R2018', audit: bool = True, replace: bool = True):
    """
    Convert a DXF file to DWG or DWG to DXF, using ODA File Converter.

    :param source: Path to the source DXF or DWG file.
    :param dest: Destination file path. If empty converts DXF <-> DWG using the same filename.
    :param version: Output version (e.g., "R2018").
    :param audit: Whether to audit the file during conversion.
    :param replace: Replace the destination file if it already exists.
    """
    source_path = Path(source)
    if dest:
        dest_path = Path(dest)
    else:
        # Generate destination filename: DXF -> DWG, DWG -> DXF
        if source_path.suffix.lower() == ".dxf":
            dest_path = source_path.with_suffix(".dwg")
        elif source_path.suffix.lower() == ".dwg":
            dest_path = source_path.with_suffix(".dxf")
        else:
            logger.error(f"Unsupported source file extension: {source_path.suffix}")
            raise odafc.UnsupportedFileFormat(f"Unsupported source file extension: {source_path.suffix}")

    logger.debug(f"Attempting to convert: {source_path} -> {dest_path}")
    odafc.convert(
        source=source_path,
        dest=dest_path,
        version=version,
        audit=audit,
        replace=replace
    )
    logger.info(f"Successfully converted: {source_path} -> {dest_path}")
