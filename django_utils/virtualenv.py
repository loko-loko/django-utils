# -*- coding: utf-8 -*-

import os
from shutil import rmtree
from loguru import logger
from django_utils.utils import cmd_exec

class DjangoVenv():

    def __init__(self, cfg, new=False):
        path = cfg.config["python"]["venv_path"]
        python_bin = cfg.config["python"]["bin"]
        pip_reqs = cfg.config["python"]["pip_requirements"]
        project_path = cfg.config["global"]["project_path"]
        if new:
            self._delete(path)
        if not self._check(path):
            self._create(path, python_bin, pip_reqs)
        self._activate(path)
        os.chdir(project_path)

    @staticmethod
    def _check(path):
        if os.path.exists(path):
            return True
        return False

    @staticmethod
    def _create(path, python_bin, pip_reqs):
        logger.info(f'[venv] Creation : {path}')
        cmd_exec(f'{python_bin} -m virtualenv {path}')
        logger.info('[venv] Installation of PIP requirements')
        cmd_exec(f'{path}/bin/python -m pip install -r {pip_reqs}')

    @staticmethod
    def _activate(path):
        logger.info(f'[venv] Activation: {path}')
        try:
            os.chdir(path)
            activate_script = os.path.join(path, 'bin', 'activate_this.py')
            exec(open(activate_script).read(), dict(__file__=activate_script))
        except Exception as e:
            logger.error('[venv] Activation problem: {e} |Exit|')

    @staticmethod
    def _delete(path):
        if self._check(path):
            logger.info(f'[venv] Delete: {path}')
            rmtree(path)
        else:
            logger.warning(f'[venv] Not Find: {path}')
