import logging
logger = logging.getLogger('txtarchve')
logger.setLevel(logging.INFO)

if not logger.hasHandlers():
    ch = logging.StreamHandler()
    logger.addHandler(logging.StreamHandler())
    logger.addHandler(logging.FileHandler('txtarchve.log'))
    ch.setLevel(logging.INFO)
    
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add formatter to console handler
    ch.setFormatter(formatter)
    
    # Add formatter to file handler
    ch.setFormatter(formatter)
    
    # Add consolo handler to logger
    logger.addHandler(ch)
    