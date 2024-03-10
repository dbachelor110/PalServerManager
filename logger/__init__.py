import logging
from logging.handlers import TimedRotatingFileHandler
from folders import OUTPUT, insureDir

# 設定 logger
LOGS = f'{OUTPUT}/logs'
insureDir(LOGS)



class ContextFilter(logging.Filter):
    '''Enhances log messages with contextual information'''
    def filter(self, record):
        record.hostname = "ServerM"
        return True
    
# 定義自訂的日誌級別（數字可以是 1-50 之間的任意整數）
DETAIL = 5

# 新增自訂的日誌級別名稱
logging.addLevelName(DETAIL, "DETAIL")

def detail(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 5.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.info("Houston, we have a %s", "interesting problem", exc_info=1)
    """
    if self.isEnabledFor(DETAIL):
        self._log(DETAIL, msg, args, **kwargs)

class Logger(logging.Logger):
    def detail(self, msg, *args, **kwargs):
        return detail(self, msg, *args, **kwargs)

# def _getLogger(name=None):
#     """
#     Return a logger with the specified name, creating it if necessary.

#     If no name is specified, return the root logger.
#     """
#     if not name:
#         return logging.root
#     return Logger.manager.getLogger(name)
    
baseFormatter = logging.Formatter(
    "({hostname})[{asctime}][{filename}:{lineno:>4}][{levelname:^7}][{thread}] - {message}",style='{')
baseHandler = TimedRotatingFileHandler(
    f"{LOGS}/ServerM.log", when="D", interval=1, backupCount=15,
    encoding="UTF-8", delay=False, utc=True)

formatter = baseFormatter

baseHandler.addFilter(ContextFilter())
baseHandler.setFormatter(formatter)
baseHandler.setLevel(10)

handler = baseHandler

def getLogger(name:str=None):
    if not name: name=__name__
    logger = Logger(name)
    logger.addHandler(handler)
    return logger