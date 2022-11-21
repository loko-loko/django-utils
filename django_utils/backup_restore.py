# -*- coding: utf-8 -*-

import os
import time
import shutil
import tarfile
from random import random
from loguru import logger
from django_utils.utils import cmd_exec, get_f_name, restart_service, check_path_o_file, check_f_ext
from django_utils.remote import HostRemote
from django_utils.s3_boto import S3Client

class DjangoBackupRestore():

    def __init__(self, args, cfg):
        self._s3 = None
        self._ssh = None
        self._remote = False

        self.env = args.env
        self.project_name = cfg["global"]["project_name"]
        self.tmp_path = cfg["global"]["tmp_path"]
        self.backup_path = cfg["backup"]["path"]
        self.remote_path = cfg["ssh"]["remote_path"]
        self.media_path = self._get_media_path(cfg["django"]["media_path"])
        self.db_name = cfg["db"]["name"]
        self.compression = cfg["backup"]["compression"]

        self.random_id = str(random())[2:8]
        self.current_date = time.strftime("%Y_%m_%d")

        if args.s3:
            self._remote = True
            self._s3 = S3Client(cfg)
        if args.ssh:
            self._remote = True
            self._ssh = HostRemote(cfg)

        if not self._remote:
            check_path_o_file(self.backup_path, 'Dir')

    @staticmethod
    def _pg_cmd(cmd):
        return f'sudo su postgres -c "{cmd}"'

    @staticmethod
    def _compress_file(fname, ftype):
        logger.info(f'[{ftype}] Compress file: {get_f_name(fname)}')
        cmd_exec(f'xz -zf9 {fname}')
        return fname + '.xz'

    @staticmethod
    def _uncompress_file(fname, ftype):
        logger.info(f'[{ftype}] Decompress file: {fname}')
        cmd_exec(f'xz -d {fname}')
        return fname.replace('.xz', '')

    def _get_archive_file(self, atype):
        archive = (f'{self.current_date}_{self.project_name}'
                   f'_{atype}.{self.env.lower()}')
        archive += ".tar" if atype == "media" else ".dump"
        if self._remote:
            return os.path.join(self.tmp_path, archive)
        return os.path.join(self.backup_path, archive)

    @staticmethod
    def _get_media_path(path):
        media_path = os.path.dirname(path)
        if media_path == path:
            logger.error(f'[media] Not find path of media: {path} |Exit|')
        return path

    def _send_to_remote(self, local_file):
        # Send file to s3
        if self._s3:
            s3_path_file = f"backup/{get_f_name(local_file)}"
            self._s3.upload_file(
                path_file=local_file,
                s3_path_file=s3_path_file)
        # Send file to ssh
        if self._ssh:
            remote_file = f'{self.remote_path}/{get_f_name(local_file)}'
            self._ssh.put_file(
                local_file=local_file,
                remote_file=remote_file)
        # Delete local file
        os.remove(local_file)

    def backup_media(self):
        backup_file = self._get_archive_file("media")
        # Create archive with media content
        logger.info(f'[backup media] Create new archive: {backup_file}')
        with tarfile.open(backup_file, 'w') as f:
            f.add(self.media_path, arcname=os.path.basename(self.media_path))
        # Compression of media archive
        if self.compression:
            backup_file = self._compress_file(backup_file, 'media')
        if self._remote:
            self._send_to_remote(backup_file)
        logger.info(f'[backup media] Success: {backup_file}')

    def restore_media(self, media_file):
        # Check extension
        check_f_ext(media_file, '.tar(.xz)?', 'media')
        tmp_file = f'{self.tmp_path}/{self.random_id}-{get_f_name(media_file)}'
        if self._remote:
            # Get backup to s3/ssh
            if self._s3:
                logger.info("Feature not implemented")
                return
            if self._ssh:
                self._ssh.get_file(remote_file=media_file, local_file=tmp_file)
        else:
            check_path_o_file(media_file, 'Media', type='File', create_path=False)
            # Move backup to temp file
            logger.info(f'[restore media] Create temp file: {tmp_file}')
            shutil.copy2(media_file, tmp_file)
        # Uncompress backup file (if .xz ext)
        if '.xz' in get_f_name(media_file):
            tmp_file = self._uncompress_file(tmp_file, "restore media")
        # Delete local media path (if present)
        if os.path.exists(self.media_path): 
            logger.info(f'[restore media] Delete old path: {self.media_path}')
            shutil.rmtree(self.media_path)
        # Untar backup file
        logger.info(f'[restore media] Untar file: {tmp_file}')
        with tarfile.open(tmp_file, 'r') as o:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(o, self.media_path)
        # Delete archive
        logger.info(f'[restore media] Delete file: {tmp_file}')
        os.remove(tmp_file)

    def backup_db(self):
        backup_file = self._get_archive_file("db")
        # Create archive with media content
        logger.info(f'[backup db] Name: {self.db_name}')
        command = self._pg_cmd(f'pg_dump {self.db_name}')
        # Start db backup
        with open(backup_file, 'wb') as f:
            cmd_exec(command, stdout=f)
        # Compression of db dump
        if self.compression:
            backup_file = self._compress_file(backup_file, 'dump')
        if self._remote:
            self._send_to_remote(backup_file)
        logger.info(f'[backup db] Success: {backup_file}')

    def restore_db(self, dump_file):
        # Check extension
        check_f_ext(dump_file, '.dump(.xz)?', 'Dump')
        tmp_file = f'{self.tmp_path}/{self.random_id}-{get_f_name(dump_file)}'
        if self._remote:
            # Get backup to s3/ssh
            if self._s3:
                logger.info("Feature not implemented")
                return
            if self._ssh:
                self._ssh.get_file(remote_file=dump_file, local_file=tmp_file)
        else:
            check_path_o_file(dump_file, 'Dump', type='File', create_path=False)
            # Move backup to temp file
            logger.info(f'[restore db] Create temp file: {tmp_file}')
            shutil.copy2(dump_file, tmp_file)

        if '.xz' in get_f_name(tmp_file):
            tmp_file = self._uncompress_file(tmp_file, "db")

        logger.info(f'[restore db] Delete: {self.db_name}')
        cmd_exec(self._pg_cmd(f'dropdb {self.db_name}'))

        logger.info(f'[restore db] Create: {self.db_name}')
        cmd_exec(self._pg_cmd(f'createdb {self.db_name}'))

        logger.info(f'[restore db] Restore: {tmp_file}')
        with open(tmp_file, 'rb') as f:
            cmd_exec(self._pg_cmd(f'psql {self.db_name}'), stdin=f)

        logger.info(f'[restore db] Delete file: {tmp_file}')
        os.remove(tmp_file)

        restart_service("postgresql")

    def backup(self, args):
        if args.db_backup:
            self.backup_db()
        if args.media_backup:
            self.backup_media()

    def restore(self, args):
        if args.db_restore:
            self.restore_db(args.dump_file)
        if args.media_restore:
            self.restore_media(args.media_file)

    def close(self):
        if self._ssh:
            self._ssh.close()
