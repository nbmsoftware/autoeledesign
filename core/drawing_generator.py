from core.layouts import LayoutRegistry
from file_utils.file_loader import load_cad_file
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DrawingGenerator:
    def __init__(self, template_path, input_data):
        self.doc = None
        self.template_path = template_path
        self.input_data = input_data

    def generate(self):
        # Load base project template (frame with tables)
        self.load_template()

        # Load landbase (property lines, subdivision boundary etc.) and place it in the template
        # todo load landbase and split/duplicate layouts if needed

        # Preprocess input data for template population
        self.process_input_data()

        # Populate templates with input data and generate needed drawings on each layout template
        logger.info("Generating all layouts dynamically")
        for layout_cls in LayoutRegistry.get_all():
            layout_instance = layout_cls(self.doc, self.input_data)
            layout_instance.edit()

        logger.info("All layouts processed successfully")
        self.doc.saveas("output.dxf")
        logger.info("Output file saved successfully")


    def load_template(self):
        logger.info("Loading project template")
        template_path = Path(self.template_path)
        if not template_path.exists():
            logger.error(f"Template not found: {template_path}")
            raise FileNotFoundError(f"Template file not found: {template_path}")

        self.doc = load_cad_file(str(template_path))
        logger.info(f"Template loaded successfully: {template_path}")


    def process_input_data(self):
        logger.debug("Processing input data")
        # Add SHEET_MAX attr - how many sheets the project has
        self.input_data["SHEET_MAX"] = len(self.doc.layouts)-1
        # Format PROJECT_TECHNICIAN value
        self.format_project_technician()


    def format_project_technician(self):
        """
        Format project technician value.
        Format: FIRST_INITIAL.LASTNAME
        :return: formatted project technician value
        """
        name = self.input_data.pop("PROJECT_TECHNICIAN", None)
        if name:
            parts = name.split()
            if len(parts) >= 2:
                initials = f"{parts[0][0]}.{parts[1]}".upper()
                self.input_data["PROJECT_TECHNICIAN"] = initials
            else:
                raise ValueError(f"Unexpected name format: {name}")
        else:
            raise KeyError("Missing required attribute: 'PROJECT_TECHNICIAN'")
