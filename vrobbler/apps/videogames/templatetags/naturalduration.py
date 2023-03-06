from django import template

register = template.Library()


@register.filter
def natural_duration(value):
    value = int(value)
    hours = int(value / 60)
    minutes = value - (hours * 60)
    value_str = ""
    if minutes:
        value_str = f"{minutes} minutes"
    if hours:
        value_str = f"{hours} hours, " + value_str
    return value_str
