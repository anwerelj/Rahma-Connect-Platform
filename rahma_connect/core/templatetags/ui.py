"""
Custom template tags and filters for Rahma Connect.
"""

from django import template
from django.utils.html import format_html

from .. import data as db

register = template.Library()


@register.filter
def badge(code, kind):
    """Display a colored badge from a status code."""
    label, color = db.STATUS_TABLES[kind].get(code, (code, "gray"))
    return format_html('<span class="badge badge-{}">{}</span>', color, label)


@register.filter
def status_label(code, kind):
    """Return just the status label without HTML."""
    return db.STATUS_TABLES[kind].get(code, (code, "gray"))[0]


@register.inclusion_tag("core/partials/stepper.html")
def stepper(kind, current):
    """Generate the status tracking stepper display."""
    steps = db.STEPS[kind]
    index = steps.index(current) if current in steps else -1
    items = []
    for i, code in enumerate(steps):
        if i < index:
            state = "done"
        elif i == index:
            state = "current"
        else:
            state = "todo"
        items.append({
            "label": db.STATUS_TABLES[kind][code][0],
            "state": state,
            "number": i + 1,
        })
    return {"items": items}
