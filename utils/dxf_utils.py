import logging

logger = logging.getLogger(__name__)

def insert_img_into_dxf(doc, image_path, insert_point, width_units, height_units, width_px, height_px):
    """
    Insert image into modelspace.

    :param doc: drawing doc
    :param image_path: path to image
    :param insert_point: image insertion point
    :param width_units: image width in CAD units
    :param height_units: image height in CAD units
    :param width_px: image width in pixels
    :param height_px: image height in pixels
    """
    image_def = doc.add_image_def(
        filename=str(image_path),
        size_in_pixel=(width_px, height_px)
    )
    doc.modelspace().add_image(
        image_def,
        insert=insert_point,
        size_in_units=(width_units, height_units),
        rotation=0
    )
    logger.info(f"Image inserted at: {insert_point}, size: {width_units} x {height_units}")
