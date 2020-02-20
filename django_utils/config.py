import os
from configparser import ConfigParser, RawConfigParser, ExtendedInterpolation
from loguru import logger

# Config default values
DEFAULT_CONFIG = {
    "global": dict(
        project_name = "django",
        project_path = "/project/${project_name}",
        log_path = "/var/log/${project_name}",
        tmp_path = "${project_path}/tmp",
    ),
    "django": dict(
        debug = 1,
        port = 9000,
        secret_key = "@secret_key",
        allowed_hosts = "127.0.0.1",
        wsgi_module = "${global:project_name}.wsgi",
        media_path = "${global:project_path}/media",
        data_path = "${global:project_path}/media/data",
        app_path = "${global:project_path}/app",
    ),
    "python": dict(
        bin = "/usr/bin/python3",
        pip_requirements = "${global:project_path}/requirements.txt",
    ),
    "db": dict(
        name = "${global:project_name}_db",
        user = "${global:project_name}_user",
        password = "@db_password",
    ),
    "backup": dict(
        path = "${global:project_path}/db_backup",
        compression = True,
    ),
    "ssh": dict(
        host = "server",
        user = "root",
        port = 22,
        remote_path = "/backup/${global:project_path}",
    ),
    "s3": dict(
        url = "http://my-s3",
        bucket = "bucket_${global:project_name}",
        access_key = "@s3_access_key",
        secret_key = "@s3_secret_key",
    ),
}

class Config():

    @staticmethod
    def _env_build(section, key):
        """
        build env var with value:
          global/project_path -> PROJECT_PATH
          db/password -> DB_PASSWORD
          django/secret_key -> DJANGO_SECRET_KEY
        """
        if section != "global":
            return f"{section.upper()}_{key.upper()}"
        return key.upper()

    @staticmethod
    def _get_arg(args, section, key, value):
        if section != "global":
            arg_value = args.get(f"{section}_{key}")
        else:
            arg_value = args.get(key, value)
        return value if not arg_value else arg_value

    @classmethod 
    def add_arguments(cls, parser):
        """
        Add default config value in arguments parser
        """
        for section, data in DEFAULT_CONFIG.items():
            for key, value in data.items():
                # Get env variables
                cfg_env = cls._env_build(section, key)
                # Generate help
                cfg_help = " ".join([k.capitalize() for k in key.split("_")])
                if section != "global":
                    cfg_option = f"{section}-{key}"
                    cfg_help = f"{section.upper()} {cfg_help}"
                else:
                    cfg_option = f"{key}"
                cfg_option = f"--{cfg_option}".replace("_", "-")
                cfg_help = f"{cfg_help} [export {cfg_env}]"
                parser.add_argument(cfg_option, help=cfg_help)
        return parser

    @classmethod
    def build(cls, args):
        """
        Build config with args, env, file and default config
        """
        file_config = ConfigParser()
        if args.config_file:
            # Read current config
            file_config.read(args.config_file)
        # Create new config builder
        config = ConfigParser(interpolation=ExtendedInterpolation())
        # Generate config values
        for section, data in DEFAULT_CONFIG.items():
            config.add_section(section)
            for key, value in data.items():
                # Get config file value (or set default value)
                if section in file_config.sections():
                    value = file_config[section].get(key, value)
                # Get env var (or set default value)
                cfg_env = cls._env_build(section, key)
                value = os.environ.get(cfg_env, value)
                # Get args (or set default value)
                value = cls._get_arg(vars(args), section, key, value)
                # Set new config value
                config.set(section, key, str(value))
        return config

    @staticmethod
    def write(config, file):
        """
        Write config file
        """
        try:
            with open(file, 'w') as f:
                config.write(f)
        except Exception as e:
            print(f"<!> Writting configuration file problem: {e}")
            exit(1)
