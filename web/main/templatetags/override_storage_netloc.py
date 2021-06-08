from django import template
from django.conf import settings

from ..utils import override_storage_netloc as override_netloc

register = template.Library()

@register.filter
def override_storage_netloc(url):
    if url:
        return override_netloc(url) if settings.OVERRIDE_STORAGE_NETLOC else url
