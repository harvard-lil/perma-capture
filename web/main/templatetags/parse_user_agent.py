from ua_parser import user_agent_parser

from django import template

register = template.Library()

@register.filter
def parse_user_agent(ua_string):

    parsed = user_agent_parser.Parse(ua_string)
    if parsed:
        return f"{parsed['user_agent']['family']} ({parsed['os']['family']})"
