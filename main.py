from config.logging_config import setup_logging
from utils.file_loader import load_json_file
from core.drawing_generator import DrawingGenerator

def main():
    setup_logging()
    data = load_json_file("data/inputs/input_data.json")
    generator = DrawingGenerator(data)
    generator.generate()

if __name__ == "__main__":
    main()
