import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - [%(levelname)s] - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s",
    filename='./logger/logger.log',
    filemode='a',
    # filemode='w',
    datefmt='%d-%b-%y %H:%M:%S'
)

logger = logging.getLogger('baggage_logger')
