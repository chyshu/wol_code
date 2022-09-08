"""
WSGI config for djproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os



from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djproject.settings')

#if Use ENV
import sys
from os.path import join,dirname,abspath
PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)
sys.path.append('/home/chyshu/newproject/venv/lib/python3.10/site-packages')


application = get_wsgi_application()




# SSL
os.environ['HTTPS'] = "on"
