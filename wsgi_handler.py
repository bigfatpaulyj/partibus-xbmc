import os
import sys

path = '%%webroot%%'
if path not in sys.path:
    sys.path.append(path)

sys.path.append('%%webroot%%/mysite')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

