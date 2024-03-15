import logging

def setup_logger():
    """
    Использую logging
    чтобы при деплое легко переключить сохранение логов в файл
    :return:
    """
    fmt = logging.Formatter(fmt="%(asctime)s %(filename)s:%(lineno)d | %(message)s", datefmt="%m/%d %H:%M:%S")
    cons = logging.StreamHandler()
    cons.setFormatter(fmt)
    logger = logging.getLogger('azzyt-binance')
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    logger.addHandler(cons)
    return logger
