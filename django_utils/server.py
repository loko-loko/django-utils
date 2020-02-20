import time
from loguru import logger
from django_utils.utils import cmd_exec

class DjangoServer():

    @classmethod
    def run(cls, env, cfg, log_file):
        port = cfg["django"]["port"]
        module = cfg["django"]["wsgi_module"]
        # Start web server
        logger.info(f"[django] Start {env} (Port:{port})")
        if env == 'dev':
            # Dev: start django server
            command = f'python3 manage.py runserver 0.0.0.0:{port}'
            with open(log_file, 'a') as f:
                cmd_exec(command, wait=False, stdout=f, stderr=f)
        elif env == 'prd':
            # Prod: start uwsgi
            command = (f'exec uwsgi --module {module} --uid=1001 --gid=1001 '
                       f'--daemonize={log_file} --socket 127.0.0.1:{port}')
            cmd_exec(command, wait=False)
        time.sleep(2)
