from django.conf import settings
from djproxy.views import HttpProxy

class ViteProxy(HttpProxy):
    base_url = f'http://localhost:{settings.VITE_PORT}/'
