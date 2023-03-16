""" 
Config logger for server
"""
import os
import logging
import logging.handlers

LOG_FILE_NAME = "server.log"

# get root folder
# Todo
root_path = "."
log_path = os.path.join(root_path, LOG_FILE_NAME)

GLOBAL_LOGGER_LEVEL = logging.NOTSET
FILE_LOGGER_LEVEL = logging.DEBUG
TERMINAL_LOGGGR_LEVEL = logging.DEBUG

logger = logging.getLogger("server")
logger.root.setLevel(GLOBAL_LOGGER_LEVEL)

logger_formater = logging.Formatter(
    "<%(asctime)s> <%(levelname)s> <%(name)s> <%(message)s>")

logger_hander_file = logging.handlers.TimedRotatingFileHandler(
    filename=log_path, when="D", interval=1, encoding="utf")
logger_hander_file.setFormatter(logger_formater)
logger_hander_file.setLevel(FILE_LOGGER_LEVEL)

logger_handler_terminal = logging.StreamHandler()
logger_handler_terminal.setFormatter(logger_formater)
logger_handler_terminal.setLevel(TERMINAL_LOGGGR_LEVEL)

logger.addHandler(logger_hander_file)
logger.addHandler(logger_handler_terminal)

logger.debug("logger Config")
