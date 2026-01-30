import logging


def getLogger(debugLevel=False) -> logging.Logger:
    """
    Returns a logger instance for the Tic Tac Toe module.
    """
    logger = logging.getLogger(__name__)

    if debugLevel:
        logger.setLevel(logging.DEBUG)
        FORMAT = "[%(levelname)s] [%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
        logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        FORMAT = "[%(levelname)s] %(message)s"
        logging.basicConfig(format=FORMAT, level=logging.INFO)
        
    return logger


if __name__ == "__main__":
    """
    Main function to demonstrate logger usage.
    """
    logger = getLogger()
    logger.info(f"Logger has been initialized with level: {logging.getLevelName(logger.level)}")