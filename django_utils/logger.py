import re
import os
import sys
import inspect

from loguru import logger

class MyFilter:

    def __init__(self, args):
        self.args = args

    def __call__(self, record):
        if '|Exit|' in record["message"]:
            logger.filter = None
            level = record["level"]
            if inspect.isclass(type(level)):
                level = level.name
            message = record["message"].replace('|Exit|', '.quit()')
            logger.log(level, message)
            if level != "ERROR":
                logger.info(f"o-> End of Script <-o")
            sys.exit()

        if self.args.silent:
            if re.search('\[\*\]|\.quit\(\)', record["message"]):
                return record
        else:
            return record

def logger_init(args, cfg):
    # Set debug True
    level = "DEBUG" if args.debug else "INFO"
    # Create Log Directory if not exist
    log_path = cfg["global"]["log_path"]
    if not os.path.exists(log_path):
        try:
            os.makedirs(log_path)
        except Exception as e:
            print(f"<!> Log path creation problem: {e}")
            exit(1)
    # Select log file name
    log_file = os.path.join(log_path, f'django_exec.{args.env}.log')
    # Init logger
    logger_filter = MyFilter(args)
    logger.remove()
    logger.add(sys.stderr, level=level, filter=logger_filter,
               format="{time:YYYY/MM/DD HH:mm:ss}  {level:<7} - {message}")
    if not args.no_log and not args.debug:
        logger.add(log_file, rotation="2 MB")
    return log_file
