# Import the registry
from .layout_registry import LayoutRegistry

# Import all layout modules so subclasses register automatically
from .cover_page import CoverPage
from .schematic import SchematicDrawing
from .electrical import ElectricalDrawing
from .civil import CivilDrawing
from .ici_design import IciDesignDrawing