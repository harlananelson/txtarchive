import logging

# Library-correct logging: only create a named logger.
# Handler configuration is the responsibility of the application entry point
# (e.g., __main__.py), not the library itself.
logger = logging.getLogger('txtarchive')
logger.addHandler(logging.NullHandler())
