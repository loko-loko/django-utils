import argparse
from configparser import ConfigParser, ExtendedInterpolation

import pytest
import testing.postgresql
import psycopg2

from django_utils.config import DEFAULT_CONFIG, Config
from django_utils.logger import Logger

def init_logger(args):
    args.debug = True
    args.no_log = True
    args.silent = False
    args.env = "test"
    Logger.build(args, "/fake/log")

def build_fake_config_file(tmpdir):
    cfg_file = tmpdir.mkdir("fake").join("config")
    cfg_file.write(
      "[global]\n"
      "project_path = /project/fake\n\n"
      "[s3]\n"
      "url = http://s3_fake_url\n"
      "bucket = bucketo\n")
    return cfg_file

def build_parser(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--config-file', default="/etc/fake/config")
    parser = Config.add_arguments(parser)
    return parser.parse_args(args)

def get_default_config():
    cfg = ConfigParser(interpolation=ExtendedInterpolation())
    cfg.read_dict(DEFAULT_CONFIG)
    return cfg

def build_fake_db():
    postgres = testing.postgresql.Postgresql()
    credentials = postgres.dsn()
    con = psycopg2.connect(**credentials)
    con.autocommit = True
    cur = con.cursor()
    return cur, credentials
