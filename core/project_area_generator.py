from ezdxf import bbox
import requests
from pyproj import Transformer
import os
from dotenv import load_dotenv
import logging
from utils.dxf_utils import insert_img_into_dxf

logger = logging.getLogger(__name__)

def generate_project_area_with_boundary(
    doc,
    xref_folder,
    boundary_layer="_SP-BLK9-PR-PHASE LIMIT",
    pad_x=100,
    pad_y=50
):
    """
    Generates a Mapbox static image of a PROJECT AREA and inserts it into modelspace next to the landbase.
    Draws a project boundary on top of the image (translated and scaled landbase boundary).

    :param doc: drawing doc
    :param xref_folder: references folder to save image into
    :param boundary_layer:  layer with boundary
    :param pad_x:   padding in pixels for x-axis
    :param pad_y:   padding in pixels for y-axis
    """
    logger.debug("Generating mapbox image for PROJECT AREA")
    # Load drawing modelspace
    msp = doc.modelspace()

    # Find project boundary points
    points_utm = get_project_boundary_points(boundary_layer, msp)

    # Compute UTM bounding box and add padding
    xs, ys = zip(*points_utm)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    expanded_ll_x = min_x - pad_x
    expanded_ll_y = min_y - pad_y
    expanded_ur_x = max_x + pad_x
    expanded_ur_y = max_y + pad_y
    logger.debug(f"Expanded bbox in UTM: X[{expanded_ll_x}, {expanded_ur_x}], Y[{expanded_ll_y}, {expanded_ur_y}]")

    # Calculate UTM height and width of expanded bounding box
    utm_height = expanded_ur_y - expanded_ll_y
    utm_width = expanded_ur_x - expanded_ll_x

    # Calculate image size in px
    height_px, width_px = get_img_height_width_px(utm_height, utm_width)

    # Generate output path for image
    output_img = xref_folder / "project_area_mapbox.png"

    # Generate bounding box string for mapbox request
    bbox_str = get_bbox_wgs_str(expanded_ll_x, expanded_ll_y, expanded_ur_x, expanded_ur_y)

    # Request Mapbox static image
    fetch_and_save_mapbox_img(bbox_str, height_px, width_px, output_img)

    # Calculate insertion point - using max coordinates (min coordinates take image far away)
    msp_bbox = bbox.extents(msp)
    insert_point = (msp_bbox.extmax.x + 100, msp_bbox.extmax.y + 100)

    # Insert image into modelspace
    insert_img_into_dxf(doc, output_img, insert_point, utm_width, utm_height, width_px, height_px)

    # Draw boundary pline on top of the image
    # Calculate scale just in case of ratio inconsistency
    scale_x = utm_width / (expanded_ur_x - expanded_ll_x)
    scale_y = utm_height / (expanded_ur_y - expanded_ll_y)

    # Translate/scale original boundary pline
    boundary_img = [
        (insert_point[0] + (x - expanded_ll_x) * scale_x,
         insert_point[1] + (y - expanded_ll_y) * scale_y)
        for x, y in points_utm
    ]
    doc.layers.new(name="MAP_BOUNDARY", dxfattribs={"color": 1})
    msp.add_lwpolyline(boundary_img, close=True, dxfattribs={"layer": "MAP_BOUNDARY"})
    logger.info("Project boundary drawn on top of the image")


def get_project_boundary_points(boundary_layer, msp):
    """
    Load boundary LW Polyline from boundary_layer in modelspace.

    :param boundary_layer:  name of the layer where the project boundary is
    :param msp: drawing modelspace
    :return: points of the boundary polyline
    """
    boundary = next(iter(msp.query(f'LWPOLYLINE[layer=="{boundary_layer}"]')), None)
    if not boundary:
        raise ValueError("No boundary polyline found in the DXF")

    points_utm = [p[:2] for p in boundary.get_points()]
    logger.debug(f"Loaded {len(points_utm)} boundary points.")

    return points_utm


def get_bbox_wgs_str(ll_x, ll_y, ur_x, ur_y):
    """
    Convert expanded bounding box to WGS84 and create a bbox string for mapbox request.

    :param ll_x:    bbox lower left x coordinate
    :param ll_y:    bbox lower left y coordinate
    :param ur_x:    bbox upper right x coordinate
    :param ur_y:    bbox upper right y coordinate
    :return: bbox string for mapbox
    """
    # CRS
    utm_epsg = 32617
    wgs84_epsg = 4326

    # Convert expanded bbox to WGS84
    to_latlon = Transformer.from_crs(utm_epsg, wgs84_epsg, always_xy=True)

    exp_min_lon, exp_min_lat = to_latlon.transform(ll_x, ll_y)
    exp_max_lon, exp_max_lat = to_latlon.transform(ur_x, ur_y)
    logger.debug(f"Expanded geographic bbox: Lon[{exp_min_lon}, {exp_max_lon}], Lat[{exp_min_lat}, {exp_max_lat}]")

    return f"[{exp_min_lon},{exp_min_lat},{exp_max_lon},{exp_max_lat}]"


def get_img_height_width_px(utm_height, utm_width):
    """
    Calculate mapbox image height and width in pixels based on UTM height and width ratio.

    :param utm_height: bbox height in UTM
    :param utm_width:  bbox width in UTM
    :return: bbox height and width in pixels
    """
    geo_ratio = utm_width / utm_height  # width / height in meters (UTM)

    max_mapbox_img_size_px = 1280
    if geo_ratio >= 1:  # landscape or square
        width_px = max_mapbox_img_size_px
        height_px = int(round(max_mapbox_img_size_px / geo_ratio))
    else:  # portrait
        height_px = max_mapbox_img_size_px
        width_px = int(round(max_mapbox_img_size_px * geo_ratio))

    # Ensure neither dimension exceeds Mapbox limits
    width_px = min(width_px, max_mapbox_img_size_px)
    height_px = min(height_px, max_mapbox_img_size_px)

    return height_px, width_px


def fetch_and_save_mapbox_img(bbox_str, height_px, width_px, output_img):
    """
    Fetch and save mapbox image from mapbox API.

    :param bbox_str: bounding box string for request
    :param height_px: image height in pixels
    :param width_px: image width in pixels
    :param output_img: path to output image
    """
    load_dotenv()
    mapbox_token = os.getenv("MAPBOX_TOKEN")

    style = "streets-v12"
    url = (
        f"https://api.mapbox.com/styles/v1/mapbox/{style}/static/"
        f"{bbox_str}/{width_px}x{height_px}"
        f"?access_token={mapbox_token}"
    )

    logger.debug("Requesting Mapbox image...")
    resp = requests.get(url)
    if resp.status_code != 200:
        raise RuntimeError(f"Mapbox API error: {resp.status_code}\n{resp.text}")

    logger.info("Generated mapbox image for PROJECT AREA")
    with open(output_img, "wb") as f:
        f.write(resp.content)
    logger.info(f"Image saved: {output_img}")