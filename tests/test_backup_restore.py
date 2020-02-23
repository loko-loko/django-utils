import os
import pytest
import tarfile

from commons import *
from django_utils.backup_restore import DjangoBackupRestore

args = build_parser([])
args.env = "test"
init_logger(args)
db_name = "fake_db"

def build_backup_restore_common_config(tmpdir):
    # init fake path
    media_path = tmpdir.mkdir("fake_media")
    backup_path = tmpdir.mkdir("fake_backup")
    tmp_path = tmpdir.mkdir("fake_tmp")
    # load default config
    cfg = get_default_config()
    # add fake path
    cfg.set("django", "media_path", media_path.strpath)
    cfg.set("backup", "path", backup_path.strpath)
    cfg.set("global", "tmp_path", tmp_path.strpath)
    cfg.set("db", "name", db_name)
    return cfg

def build_fake_media_backup_file(tmpdir, media_path):
    backup_file = tmpdir.mkdir("fake_restore").join(f"fake_media_backup.tar")
    with tarfile.open(backup_file, 'w') as f:
        f.add(media_path, arcname=os.path.basename(media_path))
    os.system(f"xz -zf9 {backup_file.strpath}")
    return backup_file.strpath + ".xz"

def build_fake_db_backup_file(tmpdir, db_name):
    backup_file = tmpdir.mkdir("fake_restore").join(f"fake_db_backup.dump")
    os.system(f"sudo su postgres -c 'createdb {db_name}'")
    os.system(f"sudo su postgres -c 'pg_dump {db_name}' | sudo su $USER -c 'tee {backup_file.strpath}'")
    os.system(f"xz -zf9 {backup_file.strpath}")
    return backup_file.strpath + ".xz"

def test_django_backup_media(tmpdir):
    cfg = build_backup_restore_common_config(tmpdir)
    # set args
    args.s3 = None
    args.ssh = None
    # init class
    backup_restore = DjangoBackupRestore(args, cfg)
    # start backup media
    backup_restore.backup_media()

def test_django_restore_media(tmpdir):
    cfg = build_backup_restore_common_config(tmpdir)
    # set args
    args.s3 = None
    args.ssh = None
    args.media_file = build_fake_media_backup_file(tmpdir, cfg["django"]["media_path"])
    # init class
    backup_restore = DjangoBackupRestore(args, cfg)
    # start restore media
    backup_restore.restore_media(args.media_file)

def test_django_backup_db(caplog, tmpdir):
    cfg = build_backup_restore_common_config(tmpdir)
    # set args
    args.s3 = None
    args.ssh = None
    # create test db
    os.system(f"sudo su postgres -c 'createdb {db_name}'")
    # init class
    backup_restore = DjangoBackupRestore(args, cfg)
    # start backup db
    backup_restore.backup_db()
    # delete test db
    os.system(f"sudo su postgres -c 'dropdb {db_name}'")

def test_django_restore_db(tmpdir):
    cfg = build_backup_restore_common_config(tmpdir)
    # set args
    args.s3 = None
    args.ssh = None
    args.dump_file = build_fake_db_backup_file(tmpdir, db_name)
    # init class
    backup_restore = DjangoBackupRestore(args, cfg)
    # start db restore
    backup_restore.restore_db(args.dump_file)
