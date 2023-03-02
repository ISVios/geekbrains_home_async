"""
CLIENT
Для проекта «Мессенджер» реализовать логирование с использованием модуля logging:

1. В директории проекта создать каталог log, в котором для клиентской и серверной сторон в отдельных модулях формата client_log_config.py и server_log_config.py создать логгеры;
2. В каждом модуле выполнить настройку соответствующего логгера по следующему алгоритму:
Создание именованного логгера;
Сообщения лога должны иметь следующий формат: "<дата-время> <уровеньважности> <имямодуля> <сообщение>";
Журналирование должно производиться в лог-файл;
На стороне сервера необходимо настроить ежедневную ротацию лог-файлов.

3. Реализовать применение созданных логгеров для решения двух задач:
Журналирование обработки исключений try/except. Вместо функции print() использовать журналирование и обеспечить вывод служебных сообщений в лог-файл;
Журналирование функций, исполняемых на серверной и клиентской сторонах при работе мессенджера.
"""
import logging

LOGGER_TERMINAL_LEVEL = logging.DEBUG
LOGGER_FILE_LEVEL = logging.ERROR

#
# open all log
logging.root.setLevel(logging.NOTSET)
logger = logging.getLogger("client")

# format
logger_format = logging.Formatter(
    "<%(asctime)s> <%(levelname)s> <%(name)s> <%(message)s>")
# file
logger_file = logging.FileHandler("client.log", encoding="utf-8")
logger_file.setLevel(LOGGER_FILE_LEVEL)
# terminal
logger_terminal = logging.StreamHandler()
logger_terminal.setLevel(LOGGER_TERMINAL_LEVEL)
# apply Formatter
logger_file.setFormatter(logger_format)
logger_terminal.setFormatter(logger_format)

# apply all handler
logger.addHandler(logger_file)
logger.addHandler(logger_terminal)

if __name__ == "__main__":
    logger.debug("debug text")
    logger.info("info text")
    logger.warning("warning text")
    logger.error("error text")
    logger.critical("critical text")
