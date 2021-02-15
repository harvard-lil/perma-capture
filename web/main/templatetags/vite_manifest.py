import json

from django import template
from django.conf import settings
from django.core.cache import cache

register = template.Library()

@register.filter
def vite_manifest(path):
    cached_manifest = cache.get('vite_manifest')
    if cached_manifest:
        data = cached_manifest
    else:
        with open(settings.VITE_MANIFEST_PATH) as manifest_file:
            data = json.load(manifest_file)
            cache.set('vite_manifest', data)

    return data[path]
