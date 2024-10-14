# your_app/templatetags/multiplicar.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    return value * arg
