import ezdxf

from core.layouts import LayoutRegistry
from core.project_area import generate_project_area_with_boundary
from data.offices import get_office_info
from utils.block_utils import copy_block_definition, replace_placeholder_text_with_block
from utils.file_loader import load_cad_file
from ezdxf.xref import Loader
from ezdxf.layouts import Paperspace
from ezdxf.math import BoundingBox
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DrawingGenerator:
    def __init__(self, input_data):
        self.doc = None
        self.input_data = input_data

        # Define paths
        self.PROJECT_ROOT = Path(__file__).resolve().parent.parent
        self.TEMPLATES_FOLDER = self.PROJECT_ROOT / "data" / "templates"
        self.OUTPUT_FOLDER = self.PROJECT_ROOT / "output"
        self.XREF_FOLDER = self.OUTPUT_FOLDER / "xref"

        # Create folders
        self._init_folders()


    def _init_folders(self):
        self.OUTPUT_FOLDER.mkdir(exist_ok=True)
        self.XREF_FOLDER.mkdir(exist_ok=True)


    def generate(self):
        # Load the landbase
        logger.info("Loading project landbase")
        self.doc = load_cad_file("data/inputs/landbase.dxf")

        # Load the template layouts
        self._load_template_layouts()

        # Add project area image in msp
        generate_project_area_with_boundary(self.doc, self.XREF_FOLDER)

        # Preprocess input data for template population
        self._process_input_data()

        # Populate templates with input data and generate needed drawings on each layout template
        logger.info("Generating all layouts dynamically")
        for layout_cls in LayoutRegistry.get_all():
            layout_instance = layout_cls(self.doc, self.input_data)
            layout_instance.edit()
        logger.info("Processed all layouts")

        # Save final DXF in output folder
        dxf_path = self.OUTPUT_FOLDER / "drawing.dxf"
        self.doc.saveas(str(dxf_path))
        logger.info(f"Saved output DXF: {dxf_path}")


    def _process_input_data(self):
        logger.debug("Processing input data")
        # Add SHEET_MAX attr - how many sheets the project has
        self.input_data["SHEET_MAX"] = len(self.doc.layouts)-1
        # Format PROJECT_TECHNICIAN value
        self._format_project_technician()
        # Add office info
        self._add_office_info()
        # Add required data about project area image
        self._add_project_area_img_input_data()


    def _add_project_area_img_input_data(self, boundary_layer="MAP_BOUNDARY", margin_factor=1.15):
        """
        Add required data about project area image from modelspace to input data.
        Required data:
            project boundary bounding box height with added margin
            project boundary centroid
        Project area image is found from modelspace based on project boundary that is in boundary_layer
        and on top of the Project area image.

        :param boundary_layer: layer in modelspace where the boundary is
        :param margin_factor: factor to determine a margin size
        """
        # Find boundary polyline in given layer
        boundary = None
        for e in self.doc.modelspace().query(f'LWPOLYLINE[layer=="{boundary_layer}"]'):
            boundary = e
            break
        if boundary is None:
            raise ValueError(f"No LWPOLYLINE found on layer '{boundary_layer}'.")

        # Compute project area bounding box and centroid & add it to input data
        bbox = BoundingBox(boundary.get_points('xy'))
        if not bbox.has_data:
            raise ValueError("Boundary bounding box is empty.")
        centroid = bbox.center  # Vec3(x, y, z)
        self.input_data["PA_MSP_CENTER_POINT"] = (centroid.x, centroid.y)
        logger.debug(f"Project area img Viewport model center (centroid): ({centroid.x:.3f}, {centroid.y:.3f})")

        # Compute project area view height & add it to input data
        height = bbox.size.y
        view_height = height * margin_factor
        self.input_data["PA_MSP_HEIGHT"] = view_height
        logger.debug(f"Project area img height in msp (with margin): {view_height:.3f}")


    def _format_project_technician(self):
        """
        Format project technician value.
        Format: FIRST_INITIAL.LASTNAME
        :return: formatted project technician value
        """
        name = self.input_data.get("PROJECT_TECHNICIAN", None)
        if not name:
            logger.info("No project technician specified. Skipping Tech import.")
            return
        parts = name.split()
        if len(parts) >= 2:
            initials = f"{parts[0][0]}.{parts[1]}".upper()
            self.input_data["PROJECT_TECHNICIAN"] = initials
        else:
            raise ValueError(f"Unexpected name format: {name}")


    def _add_office_info(self):
        """
        Add the office info to the input data based on the MUNICIPALITY from inputs.
        """
        municipality_name = self.input_data.get("MUNICIPALITY")
        if not municipality_name:
            logger.info("No municipality specified. Skipping Office info import.")
        office = get_office_info(municipality_name)
        for key, value in office.items():
            self.input_data[key.upper()] = value.upper()


    def _add_engineer_stamps(self):
        """
        Add engineer stamps to all layouts.

        -----  -----  -----  -----  -----  -----  -----  -----
        Method not used currently since stamps will be added in pdf.
        Keeping the method for possible future use.
        """
        engineer_name = self.input_data.get("SIGNING_ENGINEER")
        if not engineer_name:
            logger.info("No signing engineer specified. Skipping engineer stamp placement.")
            return
        block_name = f"ES_{engineer_name.replace(' ', '_').upper()}"

        # Load stamps library and copy the engineer stamp
        stamps_doc = load_cad_file("data/block_libraries/engineer_stamps.dxf")
        copy_block_definition(block_name, stamps_doc, self.doc)

        # Replace placeholders with the engineer stamp block reference
        replace_placeholder_text_with_block(self.doc, search_text="ENGINEER STAMP", block_name=block_name)


    def _load_landbase(self):
        """
        Load the input Landbase (property lines, subdivision boundary etc.)
        with Project Boundary into drawing modelspace.

        -----  -----  -----  -----  -----  -----  -----  -----
        Method not used since it currently creates a dxf file with error.
        Saved for possible future changes.
        [NOTE] When using this method, a template file has to be loaded in self.doc
        inside generate method -> self.doc = load_cad_file(self.template_path)
        """
        logger.debug("Importing landbase from inputs")
        landbase_dxf = load_cad_file("data/inputs/landbase.dxf")
        loader = Loader(landbase_dxf, self.doc)
        loader.load_modelspace(self.doc.modelspace())
        loader.execute()
        logger.info("Imported landbase from inputs")


    def _load_template_layouts(self):
        """
        Load template layout definitions (paperspace).
        Remove default Layout1 after importing new layouts.
        Preserve layout tab order from template.
        """
        logger.debug("Adding project template layouts")

        # Load the template DXF
        template_path = self._get_template_path()
        template_doc = ezdxf.readfile(template_path)
        loader = Loader(template_doc, self.doc)

        # Preserve layout order from template
        template_layout_order = list(template_doc.layout_names_in_taborder())[1:]

        for layout_name in template_layout_order:
            layout = template_doc.layouts.get(layout_name)
            if isinstance(layout, Paperspace):
                logger.info(f"Layout: {layout.name}, entities: {len(layout)}")
                loader.load_paperspace_layout(layout)

        loader.execute()

        # DELETE the default "Layout1" if it exists
        try:
            if "Layout1" in self.doc.layout_names_in_taborder():
                self.doc.layouts.delete("Layout1")
                logger.debug("Deleted default Layout1")
        except Exception as e:
            logger.warning(f"Could not delete Layout1: {e}")

        logger.info("Added project template layouts")


    def _get_template_path(self):
        """
        Select template file based on template type from inputs.
        Check if template file exists before returning.
        """
        template_type = self.input_data.get("TEMPLATE_TYPE", "")

        template_name = f"ALECTRA {template_type} Template.dxf"
        template_path = self.TEMPLATES_FOLDER / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_type}' not found: {template_path}")

        return template_path