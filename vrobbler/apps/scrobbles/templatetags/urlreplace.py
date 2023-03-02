from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def urlreplace(context, **kwargs):
    query = context['request'].GET.copy()
    query.update(kwargs)
    return query.urlencode()
