import os
import pytest

from commons import *

def test_config_add_arguments():
    args = build_parser(['--log-path', '/log', '--db-user', 'db'])
    # test set args
    assert args.log_path == "/log"
    assert args.db_user == "db"
    # test no set args
    assert args.project_name is None
    assert args.db_password is None

def test_config_build(tmpdir):
    # build config file
    cfg_file = build_fake_config_file(tmpdir)
    # build args
    args = build_parser([
        '--log-path', '/log',
        '--db-user', 'db',
        '--s3-bucket', 'bucketa',
        '--config-file', cfg_file.strpath])
    # set environment variable
    os.environ["DJANGO_PORT"] = "999"
    os.environ["LOG_PATH"] = "/log_env"
    # init config builder
    cfg = Config.build(args)
    # load default config
    default_cfg = get_default_config()
    # test unmodified value
    assert cfg["db"]["password"] == default_cfg["db"]["password"]
    # test modified value with args
    assert cfg["db"]["user"] == "db"
    # test modified value with os.environ
    assert cfg["django"]["port"] == os.environ["DJANGO_PORT"]
    # test modified value with os.environ not replace args
    assert cfg["global"]["log_path"] == "/log"
    # test modified value with config file
    assert cfg["s3"]["url"] == "http://s3_fake_url"
    # test modified value with config file replace by args
    assert cfg["s3"]["bucket"] == "bucketa"
