from core.layouts import LayoutRegistry
from data.offices import get_office_info
from utils.block_utils import copy_block_definition, replace_placeholder_text_with_block
from utils.file_loader import load_cad_file
import logging

logger = logging.getLogger(__name__)

class DrawingGenerator:
    def __init__(self, template_path, input_data):
        self.doc = None
        self.template_path = template_path
        self.input_data = input_data

    def generate(self):
        # Load base project template (frame with tables)
        logger.info("Loading project template")
        self.doc = load_cad_file(self.template_path)

        # Load landbase (property lines, subdivision boundary etc.) and place it in the template
        # todo load landbase and split/duplicate layouts if needed

        # Preprocess input data for template population
        self.process_input_data()

        # Add engineer stamps on all layouts
        self.add_engineer_stamps()

        # Populate templates with input data and generate needed drawings on each layout template
        logger.info("Generating all layouts dynamically")
        for layout_cls in LayoutRegistry.get_all():
            layout_instance = layout_cls(self.doc, self.input_data)
            layout_instance.edit()

        logger.info("All layouts processed successfully")
        self.doc.saveas("output.dxf")
        logger.info("Output file saved successfully")


    def process_input_data(self):
        logger.debug("Processing input data")
        # Add SHEET_MAX attr - how many sheets the project has
        self.input_data["SHEET_MAX"] = len(self.doc.layouts)-1
        # Format PROJECT_TECHNICIAN value
        self.format_project_technician()
        # Add office info
        self.add_office_info()


    def format_project_technician(self):
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


    def add_office_info(self):
        """
        Add the office info to the input data based on the MUNICIPALITY from inputs.
        """
        municipality_name = self.input_data.get("MUNICIPALITY")
        if not municipality_name:
            logger.info("No municipality specified. Skipping Office info import.")
        office = get_office_info(municipality_name)
        for key, value in office.items():
            self.input_data[key.upper()] = value.upper()


    def add_engineer_stamps(self):
        """
        Add engineer stamps to all layouts.
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