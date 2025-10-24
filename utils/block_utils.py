import logging
from ezdxf.xref import Loader, ConflictPolicy

logger = logging.getLogger(__name__)

def copy_block_definition(block_name: str, source_doc, target_doc):
    """
    Copies a block definition from source_doc to target_doc using ezdxf.xref.Loader.

    :param block_name: name of the block to copy
    :param source_doc: ezdxf document containing the source block
    :param target_doc: ezdxf document where the block will be added
    """
    source_blocks = source_doc.blocks
    target_blocks = target_doc.blocks

    # Ensure the block exists in the source document
    if block_name not in source_blocks:
        logger.error(f"Block '{block_name}' not found in source document")
        raise ValueError(f"Block '{block_name}' not found in source document")

    # Skip if already exists
    if block_name in target_blocks:
        logger.debug(f"Block '{block_name}' already exists in target document")
        return

    logger.debug(f"Importing block '{block_name}' using ezdxf.xref.Loader...")
    loader = Loader(source_doc, target_doc, conflict_policy=ConflictPolicy.KEEP)

    # Load the block layout and all its dependencies into the target doc
    loader.load_block_layout(source_doc.blocks[block_name])
    loader.execute()

    logger.info(f"Block '{block_name}' imported from the block library.")


def replace_placeholder_text_with_block(doc, search_text: str, block_name: str):
    """
    Replaces all TEXT placeholder entities containing search_text with a block reference.
    Important: set justification (align point) of text entity to MIDDLE CENTER (used as insertion point)

    :param doc: ezdxf document to modify
    :param search_text: text to search for (exact match)
    :param block_name: block name to insert
    """
    # query returns a generator, copy to list to avoid modifying while iterating
    for layout in doc.layouts:
        for entity in list(layout.query("TEXT")):
            if entity.dxf.text == search_text:
                logger.debug(f"Replacing '{search_text}' with '{block_name}'")
                insertion_point = entity.dxf.align_point
                rotation = entity.dxf.rotation

                # Add block reference
                layout.add_blockref(name=block_name, insert=insertion_point, dxfattribs={'rotation': rotation})

                # Remove the original text
                layout.delete_entity(entity)

    logger.info(f"Replaced placeholders '{search_text}' with blocks '{block_name}'")