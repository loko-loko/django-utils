#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import Python3 Include Module #
import os
import re
import sys
import argparse
from loguru import logger
from django_utils.utils import *
from django_utils.logger import Logger
from django_utils.config import Config
from django_utils.process import DjangoProcess
from django_utils.server import DjangoServer
from django_utils.manager import DjangoManager
from django_utils.backup_restore import DjangoBackupRestore

DEFAULT_CONFIG_FILE = "/etc/django_utils/config"

def check_config_file(args):
    if not os.path.exists(args.config_file):
        print(f"<WARNING> Configuration file not found: {args.config_file}")
        print(" ** Only argument and default config will be used")
        if args.config_file != DEFAULT_CONFIG_FILE:
            print(" ** You can use --config-file option for choose another config file")
            print(" ** Or use --new-config-file to generate a new default config file")

def args_parse(args_liner):
    """Argument Parse/Check"""

    parser = argparse.ArgumentParser()
    parser.add_argument('env', help='Environment (dev|prd)', choices=['dev', 'prd'])

    parser.add_argument('-f', '--config-file',
        help='Config file, default: {DEFAULT_CONFIG_FILE}',
        default=DEFAULT_CONFIG_FILE)
    parser.add_argument('--new-config-file', help='Generate a default config file')
    parser.add_argument('-s', '--start', action="store_true", help='Start web server')
    parser.add_argument('-k', '--stop', action="store_true", help='Stop web server')
    parser.add_argument('-c', '--check',
        action="store_true",
        help='Check web server status [Start if down]')
    parser.add_argument('--db-restart', action="store_true", help='Database Restart')

    parser.add_argument('--clean-mig-file', action="store_true", help='Clean app migration files')

    parser.add_argument('--db-backup', action="store_true", help='Database Backup')
    parser.add_argument('--media-backup', action="store_true", help='Media Backup')
    parser.add_argument('--db-restore', action="store_true", help='Database Restore')
    parser.add_argument('--media-restore', action="store_true", help='Media Restore')

    parser.add_argument('--dump-file',
        required=re.search('--db-restore', args_liner),
        help='Dump File to Restore [.dump(.xz)]')
    parser.add_argument('--media-file',
        required='--media-restore' in sys.argv,
        help='Media File to Restore [.tar(.xz)]')
    parser.add_argument('--ssh', action="store_true", help='SSH backup/restore')
    parser.add_argument('--s3', action="store_true", help='S3 backup/restore')

    parser.add_argument('--no-log', action="store_true", help='No output file log')
    parser.add_argument('--debug', action="store_true", help='Debug Mode')
    parser.add_argument('--silent', action="store_true", help='Silent Mode')

    parser = Config.add_arguments(parser)

    return parser.parse_args()


def main():
    start_time = time.time()
    # Argument parse
    args_liner = ' '.join(sys.argv)
    args = args_parse(args_liner)

    if not args.new_config_file:
        # Check default config
        check_config_file(args)
    # Config parse
    cfg = Config.build(args)
    if args.new_config_file:
        # Create new config file
        Config.write(cfg, args.new_config_file)
    if args.check:
        args.start = True

    # Init Script logger
    log_file = Logger.build(args, cfg)
    logger.info(f'[django utils] o-> Start (Env:{args.env.capitalize()}) <-o')

    # Check and Change directory to project path
    project_path = cfg["global"]["project_path"]
    check_path_o_file(project_path, 'Project', create_path=False)
    os.chdir(project_path)

    # Check existing media path
    if not re.search("-restore", args_liner):
        check_path_o_file(cfg["django"]["media_path"], 'Media', create_path=False)

    # Init process info
    process = DjangoProcess(args.env)
    # Get process status
    procs = process.check(exit_if_active=args.check)
    # Stop server process
    if args.stop:
        process.stop(procs, exit_if_stop=True)

    # Clean Migrations File #
    if args.clean_mig_file:
        DjangoManager.clean_migration_file(cfg)

    # Backup/Restore #
    if re.search("-(backup|restore)", args_liner):
        backrest = DjangoBackupRestore(args, cfg)
        if re.search("-backup", args_liner):
            # Backup #
            backrest.backup(args)
        if re.search("-restore", args_liner):
            # Restore #
            backrest.restore(args)
        backrest.close()

    # Start server process
    if args.start:
        if procs:
            process.stop(procs)
        # Start django server
        DjangoServer.run(env=args.env, cfg=cfg, log_file=log_file)
        process.check(exit_if_not_active=True)
        # Restart service
        if args.db_restart:
            restart_service('postgresql')
        if args.env == 'prd':
            restart_service('nginx')

    logger.info(f"[log] file: {log_file}")
    exec_time = time.strftime("%H:%M:%S", time.gmtime((time.time() - start_time)))
    logger.info(f"[django utils] o-> End ({exec_time}) <-o")
