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
        self.add_project_area_viewport()


    def add_project_area_viewport(self, paper_center=(436.160, 285.743), paper_width=444.1, paper_height=292.1):
        """
        Create viewport to the project area image in modelspace.

        :param paper_center: center of the viewport on the paperspace - insertion point
        :param paper_width: width of the viewport on the paperspace
        :param paper_height: height of the viewport on the paperspace
        :return:
        """
        centroid = self.block_attrs["PA_MSP_CENTER_POINT"]
        view_height = self.block_attrs["PA_MSP_HEIGHT"]
        viewport = self.layout.add_viewport(
            center=paper_center,  # center in paperspace
            size=(paper_width, paper_height),  # viewport width and height in paper units
            view_center_point=centroid,  # center of view in modelspace
            view_height=view_height  # height visible in model units
        )
        viewport.dxf.layer = "VIEWPORTS"
        logger.info("Created project area viewport for Cover Page")
