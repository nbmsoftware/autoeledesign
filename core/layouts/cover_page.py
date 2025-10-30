from core.layouts.base_layout import BaseLayout
import logging

logger = logging.getLogger(__name__)

class CoverPage(BaseLayout):
    layout_name = "COV-01"

    def add_layout_specific_attrs(self):
        self.block_attrs["SCALE"] = 'N.T.S'

    def edit_specific(self):
        logger.info(f"Custom edits for {self.layout_name}")
        # Add a viewport to project area image in msp
        self.add_project_area_viewport(paper_center=(436.160, 285.743), paper_width=444.1, paper_height=292.1)
