import logging
from ezdxf.entities import Insert
from config.viewport_config import VIEWPORT_CONFIG

logger = logging.getLogger(__name__)

class BaseLayout:
    """
    Base class for all layout (paperspace) editors.

    Provide common functionality for shared block attributes.
    Subclasses must implement `edit_specific()` to handle layout-specific logic.
    Register all subclasses with LayoutRegistry to enable dynamic discovery of layouts in
    the DrawingGenerator.

    :ivar doc: The DXF document object (ezdxf.DXFDocument) being edited.
    :ivar block_attrs: Dictionary of input data including shared and layout-specific attributes.
    :ivar layout_name: Name of the layout in the DXF file. Must be overridden in subclasses.
    :ivar layout: The specific layout object retrieved from the document.
    """

    layout_name = None

    def __init_subclass__(cls, **kwargs):
        """
        Called automatically when a subclass is created.
        Register the subclass in LayoutRegistry for dynamic discovery.
        """
        super().__init_subclass__(**kwargs)
        if cls is not BaseLayout:
            from core.layouts.layout_registry import LayoutRegistry
            LayoutRegistry.register(cls)

    def __init__(self, doc, block_attrs):
        """
        Initialize the layout editor.

        :param doc: The DXF document being edited.
        :param block_attrs: Dictionary containing shared and layout-specific inputs.
        """
        self.doc = doc
        self.block_attrs = block_attrs
        if not self.layout_name:
            raise ValueError(f"{self.__class__.__name__} must define layout_name")
        self.layout = self.doc.layouts.get(self.layout_name)


    def edit(self):
        """
        Edit a layout template.
        """
        self.add_block_attrs()

        # Populate all block attributes in this layout
        for entity in self.layout.query("INSERT"):
            if isinstance(entity, Insert):
                for attrib in entity.attribs:
                    tag = attrib.dxf.tag
                    if tag in self.block_attrs:
                        attrib.dxf.text = self.block_attrs[tag]
                        logger.debug(f"[ATTRIB] Updated {tag} with {attrib.dxf.text}")

        # Add project area viewport
        self._add_project_area_viewport()

        # Continue with layout specific editing from subclass
        self.edit_specific()


    def add_block_attrs(self):
        """
        Add additional layout specific attributes.
        """
        # Add current sheet number
        self.block_attrs["SHEET"] = self.find_current_sheet_number()
        # Add drawing number
        self.block_attrs["DRAWING_NUMBER"] = self.generate_drawing_number()
        # Add layout specific attributes from subclass
        self.add_layout_specific_attrs()


    def find_current_sheet_number(self):
        """
        Find the current sheet (layout) number.
        :return: sheet number, None if no sheet is found
        """
        layouts = self.doc.layout_names_in_taborder()
        return next((i for i, layout_name in enumerate(layouts) if layout_name == self.layout_name), None)


    def generate_drawing_number(self):
        """
        Generate a drawing number. e.g. 123456-MODEL-01
        Format: {work_order}-{layout_name}
        :return: drawing number
        """
        project_work_order = self.block_attrs.get("PROJECT_WORK_ORDER")
        if project_work_order is None:
            raise KeyError("Missing required attribute for drawing number generation: 'PROJECT_WORK_ORDER'")
        return project_work_order + '-' + self.layout_name


    def _add_project_area_viewport(self):
        """
        Create viewport to the project area image based on VIEWPORT_CONFIG.
        """
        template_type = self.block_attrs.get("TEMPLATE_TYPE", "")

        # Determine if layout is default layout or cover page
        is_cover = "COV" in self.layout_name
        page_type = "cov" if is_cover else "default"

        # Retrieve viewport config
        viewport_config = VIEWPORT_CONFIG.get(template_type, {}).get(page_type, {})
        if not viewport_config or template_type not in VIEWPORT_CONFIG or page_type not in VIEWPORT_CONFIG[template_type]:
            raise ValueError(
                f"Missing viewport configuration for '{template_type}' ({page_type})"
            )
        paper_center = viewport_config["paper_center"]
        paper_width = viewport_config["paper_width"]
        paper_height = viewport_config["paper_height"]

        centroid = self.block_attrs["PA_MSP_CENTER_POINT"]
        view_height = self.block_attrs["PA_MSP_HEIGHT"]

        viewport = self.layout.add_viewport(
            center=paper_center,  # center in paperspace
            size=(paper_width, paper_height),  # viewport width and height in paper units
            view_center_point=centroid,  # center of view in modelspace
            view_height=view_height  # height visible in model units
        )
        viewport.dxf.layer = "VIEWPORTS"
        logger.info(f"Created project area viewport in {self.layout_name} layout.")


    def add_layout_specific_attrs(self):
        """
        Add additional layout specific attributes.
        Subclasses must implement this method with layout-specific logic.

        :raises NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement edit_specific()")


    def edit_specific(self):
        """
        Layer specific edit method.
        Subclasses must implement this method with layout-specific logic.

        :raises NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement edit_specific()")

