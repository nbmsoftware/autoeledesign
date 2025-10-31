from core.layouts.base_layout import BaseLayout
import logging

logger = logging.getLogger(__name__)

class SchematicDrawing(BaseLayout):
    layout_name = "SCH-01"

    def add_layout_specific_attrs(self):
        self.block_attrs["SCALE"] = 'N.T.S'

    def edit_specific(self):
        logger.info(f"Custom edits for {self.layout_name}")