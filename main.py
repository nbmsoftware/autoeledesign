from config.logging_config import setup_logging
from file_utils.file_loader import load_json_file
from core.drawing_generator import DrawingGenerator

def main():
    setup_logging()
    data = load_json_file("data/inputs/input_data.json")
    generator = DrawingGenerator("data/templates/ALECTRA ArchD (24x36) Template.dxf", data)
    generator.generate()

if __name__ == "__main__":
    main()
