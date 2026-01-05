import logging

def setup_logger():
    """Set up and configure the txtarchve logger."""
    logger = logging.getLogger('txtarchve')
    logger.setLevel(logging.INFO)
    
    # [FIX] Stop this logger from passing events to the root logger
    # This prevents the double-printing when basicConfig is used elsewhere
    logger.propagate = False 
    
    # Only add handlers if none exist already
    if not logger.handlers:
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # File handler
        file_handler = logging.FileHandler('txtarchve.log')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger

# Create and configure the logger
logger = setup_logger()