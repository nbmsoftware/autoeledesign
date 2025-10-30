from core.layouts.base_layout import BaseLayout
import logging

logger = logging.getLogger(__name__)

class ElectricalDrawing(BaseLayout):
    layout_name = "ELE-01"

    def add_layout_specific_attrs(self):
        # todo import correct scale from inputs
        self.block_attrs["SCALE"] = '1:500'

    def edit_specific(self):
        logger.info(f"Custom edits for {self.layout_name}")
        # Add a viewport to project area image in msp
        self.add_project_area_viewport()