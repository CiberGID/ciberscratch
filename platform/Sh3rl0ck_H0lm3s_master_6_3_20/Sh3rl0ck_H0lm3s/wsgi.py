"""
WSGI config for Sh3rl0ck_H0lm3s project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sh3rl0ck_H0lm3s.settings')

application = get_wsgi_application()
