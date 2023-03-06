from django import template

register = template.Library()


@register.filter
def natural_duration(value):
    value = int(value)
    total_minutes = int(value / 60)
    hours = int(total_minutes / 60)
    minutes = total_minutes - (hours * 60)
    value_str = ""
    if minutes:
        value_str = f"{minutes} minutes"
    if hours:
        value_str = f"{hours} hours, " + value_str
    return value_str
