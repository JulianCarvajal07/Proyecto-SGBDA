from django import template

register = template.Library()

@register.filter
def chunk(value, chunk_size):
    """Divide una lista en sublistas de tamaño chunk_size"""
    try:
        chunk_size = int(chunk_size)
    except (ValueError, TypeError):
        return [value]
    return [value[i:i + chunk_size] for i in range(0, len(value), chunk_size)]