# -*- coding: utf-8 -*-

"""
Copyright (C) 2021, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# ConcurrentLogHandler - updates stlidb's logging config on import so this needs to stay
import cloghandler
cloghandler = cloghandler # For pyflakes

# stdlib
import logging
import os

# MySQL
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# Django
import django
from django.core.management import call_command, execute_from_command_line

# Zato
from zato.admin.zato_settings import update_globals
from zato.common.json_internal import loads
from zato.common.repo import RepoManager
from zato.common.util.api import store_pidfile
from zato.common.util.open_ import open_r

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(process)d:%(threadName)s - %(name)s:%(lineno)d - %(message)s')

logger = logging.getLogger(__name__)

def main():

    store_pidfile(os.path.abspath('.'))
    repo_dir = os.path.join('.', 'config', 'repo')

    # Update Django settings
    config = loads(open_r(os.path.join(repo_dir, 'web-admin.conf')).read())
    config['config_dir'] = os.path.abspath('.')
    update_globals(config)

    os.environ['DJANGO_SETTINGS_MODULE'] = 'zato.admin.settings'

    django.setup()

    call_command('migrate')
    call_command('loaddata', os.path.join(repo_dir, 'initial-data.json'))

    RepoManager(repo_dir).ensure_repo_consistency()
    execute_from_command_line(['zato-web-admin', 'runserver', '--noreload', '--nothreading', '{host}:{port}'.format(**config)])

if __name__ == '__main__':
    main()
