#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import signal
import getpass
from loguru import logger
from django_utils.utils import cmd_exec

class DjangoProcess():
    
    def __init__(self, env):
        self.name = self._get_name(env)

    @staticmethod
    def _get_name(env):
        if env == 'prd':
            name = 'uwsgi'
        elif env == 'dev':
            name = 'manage.py'
        return name

    @staticmethod
    def _get_current_user():
        return getpass.getuser()

    def get_list(self):
        cmd = cmd_exec('ps -ef', cmd_return=True)
        procs = [dict(owner=p.split()[0], id=p.split()[1]) 
                    for p in cmd if re.search(f'{self.name}', p)]
        logger.debug(f'[process] ID list : {procs}')
        return procs

    def _check_owners(self, procs):
        # Check process owners
        logger.debug(f'[process] Get process owners')
        current_user = self._get_current_user()
        if any([current_user != p["owner"] for p in procs]):
            logger.error(f"[process] Owner process different than current user ({current_user}) |Exit|")

    def check(self, exit_if_active=False, exit_if_not_active=False):
        procs = self.get_list()
        level = "INFO"
        if not procs:
            msg = f"[process][*] No active process of {self.name}"
            if exit_if_not_active:
                level = "ERROR"
                msg += "|Exit|"
            elif exit_if_active:
                level = "WARNING"
            logger.log(level, msg)
            return False
        else:
            msg = (f"[process][*] Active process of {self.name} "
                   f"(Proc:{','.join([p['id'] for p in procs])})")
            if exit_if_active:
                msg += "|Exit|"
            logger.log(level, msg)
        return procs

    def stop(self, procs, exit_if_stop=False):
        # Kill process
        if procs:
            self._check_owners(procs)
            logger.info(f'[process] Kill {self.name} process ({len(procs)}).')
            try:
                for proc in procs:
                    os.kill(int(proc["id"]), signal.SIGKILL)
                    time.sleep(1)
            except:
                logger.error(f'[Process] Kill Problem for {self.name} |Exit|')
        if exit_if_stop:
            logger.info(f"[process] Django is stop |Exit|")
