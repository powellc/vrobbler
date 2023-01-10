# cli.py
import logging
import sys
from os import environ as env


if not 'DJANGO_SETTINGS_MODULE' in env:
    from vrobbler import settings

    env.setdefault('DJANGO_SETTINGS_MODULE', settings.__name__)


import django

django.setup()

# this line must be after django.setup() for logging configure
logger = logging.getLogger('vrobbler')


def main():
    # to get configured settings
    from django.conf import settings

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
