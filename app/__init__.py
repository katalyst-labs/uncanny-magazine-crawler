import logging
import os
import sys


logging.basicConfig(
    handlers=[
        logging.FileHandler(
            filename=r"./log_file.log",
            encoding="utf-8",
            mode="a",
        )
    ],
    format="time: %(asctime)s, level: %(levelname)s, \nmodule: %(name)s, line_no: %(lineno)s, \nmsg:%(message)s \n",
    datefmt="[ %A, %d %B - %Y | %H:%M:%S GMT %z]",
    level=logging.DEBUG,
)


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        # Will call default excepthook
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        # Create a critical level log message with info from the except hook.
    logger.critical(
        "Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback)
    )
    raise


# Assign the excepthook to the handler
sys.excepthook = handle_unhandled_exception

logger = logging.getLogger(__name__)
logger.info("Completed configuring logger()!")


# Set some defaults

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
logger.info("Starting application...")
