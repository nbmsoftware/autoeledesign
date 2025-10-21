import logging

logger = logging.getLogger(__name__)

class LayoutRegistry:
    """
    Central registry for managing all layout (paperspace) subclasses.
    Dynamically register and retrieve all layout classes that inherit from a common base class.

    Attributes:
    :ivar _registry: Internal list storing references to all registered layout classes.
    """
    _registry = []

    @classmethod
    def register(cls, layout_class):
        """
        Register a new layout class into the registry.

        :param layout_class: The layout class to register (a subclass of BaseLayout).
        """
        logger.debug(f"Registering layout class: {layout_class.__name__}")
        cls._registry.append(layout_class)

    @classmethod
    def get_all(cls):
        """
        Retrieve all registered layout classes.

        :return: A list of registered layout classes.
        """
        return cls._registry