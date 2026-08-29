"""Template filters for rendering form fields consistently.

Django templates cannot pass arguments to widget rendering, so this filter
exists to attach the accessibility attributes that tie an input to its error
message. Shared by every form in PharmaFlowAI.
"""

from django import template

register = template.Library()


@register.filter
def input_field(bound_field):
    """Render a form widget with error-aware ARIA attributes.

    Usage::

        {{ form.username|input_field }}

    Adds ``aria-describedby`` pointing at the field's error paragraph — and its hint
    paragraph when the field has help text — plus ``aria-invalid`` when the bound
    field failed validation.
    """
    described_by = [f"{bound_field.auto_id}-error"]
    if bound_field.help_text:
        described_by.append(f"{bound_field.auto_id}-hint")

    attrs = {"aria-describedby": " ".join(described_by)}
    if bound_field.errors:
        attrs["aria-invalid"] = "true"
    return bound_field.as_widget(attrs=attrs)
