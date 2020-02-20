# -*- coding: utf-8 -*-

import os
import re
from random import random
import paramiko
from scp import SCPClient
from loguru import logger
from django_utils.utils import get_f_name, cmd_exec

# logging.getLogger("paramiko").setLevel(logging.CRITICAL)

class HostRemote():

    def __init__(self, cfg):
        credentials = self._build_credentials(cfg)

        self._ssh = self._ssh_client(**credentials)
        self._scp = self._scp_client(self._ssh)

    @staticmethod
    def _build_credentials(cfg):
        return {"hostname": cfg["ssh"]["host"],
                "username": cfg["ssh"]["user"],
                "port": cfg["ssh"]["port"]}

    @staticmethod
    def _ssh_client(**kwargs):
        logger.debug(f'[ssh] Host: {kwargs["hostname"]}, '
                     f'User: {kwargs["username"]}, '
                     f'Port: {kwargs["port"]}')
        # Get private key
        priv_key_file='~/.ssh/id_rsa'
        logger.debug(f'[ssh] Get private key file : {priv_key_file}')
        try:
            priv_key_file = os.path.expanduser('~/.ssh/id_rsa')
            priv_key = paramiko.RSAKey.from_private_key_file(priv_key_file)
            kwargs['pkey'] = priv_key
        except Exception as e:
            logger.error(f"[ssh] Get private key problem: {e} |Exit|")
        # Initialize paramiko ssh client
        logger.info('[ssh] Initilialize client')
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(**kwargs)
        except Exception as e:
            logger.error(
                f'[ssh] Connection to host {credentials["hostname"]} problem: {e} |Exit|'
            )
        return client

    @staticmethod
    def _scp_client(ssh_client):
        logger.info('[scp] Initilialize client')
        return SCPClient(ssh_client.get_transport())

    def _ssh_cmd(self, cmd):
        logger.debug(f'[ssh] Command: {cmd}')
        try:
            # Execution of ssh command
            stdin, stdout, stderr = self._ssh.exec_command(cmd)
            stdout.channel.settimeout(30)
            stdin.close()
        except:
            logger.error(f'[ssh] Command: {cmd} timeout |Exit|')
        if stdout.channel.recv_exit_status() != 0:
            logger.error(f'[ssh] Command: {cmd} problem |Exit|')
        return stdout.read().decode('utf-8', 'ignore')

    def _scp_get(self, remote_file, local_file):
        logger.info(f'[scp] Get file')
        try:
            self._scp.get(remote_file, local_file)
        except Exception as e:
            logger.error(f"[scp] Get file problem: {e} |Exit|")
        logger.info(f'[scp] Get file success: {remote_file}')

    def _scp_put(self, local_file, remote_file):
        logger.info(f'[scp] Put file: {local_file}')
        try:
            self._scp.put(local_file, remote_file)
        except Exception as e:
            logger.error(f"[scp] Put Problem: {e} |Exit|")
        logger.info(f'[scp] Put success: {remote_file}')

    def _check_file(self, path, ptype='F'):
        logger.info(f'[remote] Check: {path}')
        cmd_return = self._ssh_cmd(f'ls -ld {path}')

        if 'No such file or directory' in cmd_return:
            logger.error(f'[ssh] Path not find: {path} |Exit|')
        elif ptype == 'F' and re.search('^d', cmd_return):
            logger.error(f'[ssh] File is a directory: {path} |Exit|')
        elif ptype == 'D' and re.search('^-', cmd_return):
            logger.error(f'[ssh] Not a directory: {path} |Exit|')

    def get_file(self, remote_file, local_file, ptype="F"):
        """ Get file to remote host """
        # Check if remote file exist
        self._check_file(remote_file, ptype=ptype)
        self._scp_get(remote_file, local_file)

    def put_file(self, local_file, remote_file):
        """ Put file to remote host """
        # Check if remote path exist
        remote_path = os.path.dirname(remote_file)
        self._check_file(remote_path, ptype='D')
        self._scp_put(local_file, remote_file)

    def _ssh_close(self):
        """ Close ssh connection """
        logger.debug('[ssh] Close connection')
        self._ssh.close()

    def _scp_close(self):
        """ Close scp connection """
        logger.debug('[scp] Close connection')
        self._scp.close()

    def close(self):
        self._ssh_close()
        self._scp_close()
