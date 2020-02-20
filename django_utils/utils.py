# -*- coding: utf-8 -*-

import os
import re
import sys
import time
from base64 import b64decode
from subprocess import Popen, PIPE, STDOUT
from loguru import logger

# File/Path #

def check_path_o_file(path, path_name, type='Path', create_path=True):
    if not os.path.exists(path):
        msg = f'[check] {path_name} {type} not exist: {path}'

        if create_path:
            logger.warning(msg)
        else:
            logger.error(f'{msg} |Exit|')

        if type == 'Path' and create_path:
            logger.info(f'[check] Creation {path_name} {type}')
            try:
                os.makedirs(path)
            except:
                logger.error('[check] Creation Problem |Exit|')

def get_f_name(path):
    return path.split('/')[-1]

def check_f_ext(file, ext_rgx, file_type):
    if not re.search(r'.*{0}?$'.format(ext_rgx), get_f_name(file)):
        logger.error(
            f'[{file_type}] File Bad Format [{ext_rgx} Only] : {get_f_name(file)} |Exit|'
        )

def b64_decode(data):
    return b64decode(data).decode('utf-8', 'ignore').replace('\n', '')

def cmd_exec(cmd, wait=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cmd_return=False):
    logger.debug(f'[command] {cmd}')
    popen = Popen(
        cmd,
        shell=True,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        encoding='utf-8')
    if wait and popen.wait() != 0:
        logger.debug(f'[command] Return : {pformat(popen.stdout.readlines())}')
        logger.error(f'[command] Problem : {cmd} |Exit|')
    if cmd_return:
        return popen.stdout.readlines()

def restart_service(service):
    logger.info(f'[service] Restart: {service.capitalize()}')
    cmd_exec(f'sudo systemctl restart {service}')
