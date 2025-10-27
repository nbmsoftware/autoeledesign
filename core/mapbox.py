import ezdxf
from ezdxf import bbox
import requests
from pyproj import Transformer
import os
from dotenv import load_dotenv

def generate_mapbox_image_with_boundary(
    dxf_path,
    mapbox_token,
    output_img="mapbox_bbox_image.png",
    style="streets-v12",
    utm_epsg=32617,
    wgs84_epsg=4326
):
    """
    Generates a Mapbox static image for a DXF boundary
    and inserts it next to the landbase, drawing the boundary scaled.
    """
    # Load DXF
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    # Find project boundary
    boundary = next(iter(msp.query('LWPOLYLINE[layer=="_SP-BLK9-PR-PHASE LIMIT"]')), None)
    if not boundary:
        raise ValueError("No boundary polyline found in the DXF")

    points_utm = [p[:2] for p in boundary.get_points()]
    print(f"Loaded {len(points_utm)} boundary points.")

    # Compute UTM bounding box and add padding
    xs, ys = zip(*points_utm)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    pad_x = 200
    pad_y = 100

    expanded_ll_x = min_x - pad_x
    expanded_ll_y = min_y - pad_y
    expanded_ur_x = max_x + pad_x
    expanded_ur_y = max_y + pad_y

    print(f"Expanded bbox in UTM: X[{expanded_ll_x}, {expanded_ur_x}], Y[{expanded_ll_y}, {expanded_ur_y}]")

    # Convert expanded bbox to WGS84
    to_latlon = Transformer.from_crs(utm_epsg, wgs84_epsg, always_xy=True)
    exp_min_lon, exp_min_lat = to_latlon.transform(expanded_ll_x, expanded_ll_y)
    exp_max_lon, exp_max_lat = to_latlon.transform(expanded_ur_x, expanded_ur_y)

    print(f"Expanded geographic bbox: Lon[{exp_min_lon}, {exp_max_lon}], Lat[{exp_min_lat}, {exp_max_lat}]")

    # Calculate image size in px
    max_px = 1280 # max width/height px size for MapBox

    utm_width = expanded_ur_x - expanded_ll_x
    utm_height = expanded_ur_y - expanded_ll_y
    geo_ratio = utm_width / utm_height  # width / height in meters

    if geo_ratio >= 1:  # landscape or square
        width_px = max_px
        height_px = int(round(max_px / geo_ratio))
    else:  # portrait
        height_px = max_px
        width_px = int(round(max_px * geo_ratio))

    # Ensure neither dimension exceeds Mapbox limits
    width_px = min(width_px, max_px)
    height_px = min(height_px, max_px)

    bbox_str = f"[{exp_min_lon},{exp_min_lat},{exp_max_lon},{exp_max_lat}]"

    # Request Mapbox static image
    url = (
        f"https://api.mapbox.com/styles/v1/mapbox/{style}/static/"
        f"{bbox_str}/{width_px}x{height_px}"
        f"?access_token={mapbox_token}"
    )

    print("Requesting Mapbox image...")
    resp = requests.get(url)
    if resp.status_code != 200:
        raise RuntimeError(f"Mapbox API error: {resp.status_code}\n{resp.text}")

    with open(output_img, "wb") as f:
        f.write(resp.content)
    print(f"Image saved → {output_img}")

    # Map boundary into image coordinate space

    # Calculate insertion point - using max coordinates - min takes image far away
    msp_bbox = bbox.extents(msp)
    insert_point = (msp_bbox.extmax.x + 100, msp_bbox.extmax.y + 100)

    # Calculate scale just in case of ratio inconsistency
    scale_x = utm_width / (expanded_ur_x - expanded_ll_x)
    scale_y = utm_height / (expanded_ur_y - expanded_ll_y)

    boundary_img = [
        (insert_point[0] + (x - expanded_ll_x) * scale_x,
         insert_point[1] + (y - expanded_ll_y) * scale_y)
        for x, y in points_utm
    ]

    # Insert image and draw boundary
    image_def = doc.add_image_def(filename=output_img, size_in_pixel=(width_px, height_px))
    msp.add_image(image_def, insert=insert_point, size_in_units=(utm_width, utm_height), rotation=0)

    doc.layers.new(name="MAP_BOUNDARY", dxfattribs={"color": 1})
    msp.add_lwpolyline(boundary_img, close=True, dxfattribs={"layer": "MAP_BOUNDARY"})

    print(f"Image inserted at: {insert_point}, size: {utm_width} x {utm_height}")
    output_dxf = "landbase_with_map.dxf"
    doc.saveas(output_dxf)
    print(f"Saved DXF with map and boundary → {output_dxf}")



if __name__ == "__main__":

    load_dotenv()

    generate_mapbox_image_with_boundary(
        dxf_path="../data/inputs/landbase.dxf",
        mapbox_token=os.getenv("MAPBOX_TOKEN")
    )
