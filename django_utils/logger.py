import re
import os
import sys
import inspect

from loguru import logger

class Filter:

    def __init__(self, args):
        self.args = args

    def __call__(self, record):
        if '|Exit|' in record["message"]:
            logger.filter = None
            level = record["level"]
            if inspect.isclass(type(level)):
                level = level.name
            message = record["message"].replace('|Exit|', '[quit()]')
            logger.log(level, message)
            if level != "ERROR":
                logger.info(f"[django utils] o-> End <-o")
            exit()

        if self.args.silent:
            if re.search('\[\*\]|\[quit\(\)\]', record["message"]):
                return record
        else:
            return record

class Logger():

    @classmethod
    def build(cls, args, log_path):
        """
        Build logger
        """
        log_file = None
        # Init filter
        lfilter = Filter(args)
        # Define log filter
        lformat = "{time:YYYY/MM/DD HH:mm:ss}  {level:<7} - {message}"
        # Get log level
        llevel = cls._get_log_level(args.debug)
        # Remove default logger
        logger.remove()
        # Add stderr logger
        logger.add(
            sys.stderr, level=llevel,
            filter=lfilter, format=lformat)
        if not args.no_log and not args.debug:
            # Get log file
            log_file = cls._get_log_file(log_path, args.env)
            # Add file logger
            try:
                logger.add(
                    log_file, level=llevel,
                    format=lformat, rotation="2 MB")
            except Exception as e:
                logger.error(f"[log] File problem: {e} |Exit|")
        return log_file

    @staticmethod
    def _get_log_file(log_path, env):
        """
        Check log path and define log file
        """
        # Create Log directory if not exist
        if not os.path.exists(log_path):
            try:
                os.makedirs(log_path)
            except Exception as e:
                print(f"<!> Log path creation problem: {e}")
                exit(1)
        # Select log file
        log_file = os.path.join(
            log_path, f'django_utils.{env}.log')
        return log_file

    @staticmethod
    def _get_log_level(debug):
        """
        Return log level
        """
        return "DEBUG" if debug else "INFO"
