# -*- coding: utf-8 -*-

import os
from loguru import logger
from django_utils.utils import get_f_name, cmd_exec, check_path_o_file

class DjangoManager():

    @staticmethod
    def _get_manage_file(cfg):
        file = f"{cfg['global']['project_path']}/manage.py"
        check_path_o_file(file, 'manage.py', type='File', create_path=False)
        return file

    @staticmethod
    def _get_app_path(cfg):
        path = cfg['django']['app_path']
        check_path_o_file(path, 'app', create_path=False)
        return path

    @classmethod
    def clean_migration_file(cls, cfg):
        manage = cls._get_manage_file(cfg)
        app_path = cls._get_app_path(cfg)
        find_file = False
        app_dirs = [os.path.join(app_path, d) 
                    for d in os.listdir(app_path) if not '__' in d]

        logger.info(f'[Migration] Check on App Path : {app_path}')
        logger.info((
            f'[Migration] {len(app_dirs)} App(s) Dir : '
            f'{",".join([get_f_name(a) for a in app_dirs])}'
        ))

        for app_dir in app_dirs:
            app_name = get_f_name(app_dir)
            mig_path = os.path.join(app_dir, 'migrations')

            if not os.path.exists(mig_path):
                logger.info(f'[Migration] No Migration Path for App : {app_name}')
                continue

            mig_files = [os.path.join(mig_path, f) \
                for f in os.listdir(mig_path) if not '__' in f]

            logger.debug(
                f'[Migration][{app_name}] Files : {[get_f_name(m) for m in mig_files]}'
            )

            if not mig_files:
                logger.warning(f'[Migration] No Migration File for App : {app_name}')
                continue

            for mig_file in mig_files:
                logger.info(
                    f'[Migration] Delete File {get_f_name(mig_file)} (App:{app_name})'
                )
                os.remove(mig_file)
                find_file = True

        if find_file:
            logger.info('[Migration] Execute : manage.py makemigrations')
            makemig_cmd = cmd_exec(
                f'python {manage} makemigrations',
                cmd_return=True
            )

            if 'No changes detected' in ' '.join(makemig_cmd):
                logger.warning('[Migration] No Change')

            else:
                logger.info('[Migration] Execute : manage.py migrate')
                mig_cmd = cmd_exec(logger, f'python {manage} migrate')
