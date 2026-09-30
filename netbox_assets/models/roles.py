from django.db import models

from netbox.models import NestedGroupModel
from utilities.fields import ColorField


class AssetRole(NestedGroupModel):
    """
    Functional role of an Asset (e.g. Router, Switch, SFP, Line Card).
    Roles can be nested. Similar to DeviceRole in NetBox core.
    """

    name = models.CharField(
        max_length=100,
    )
    slug = models.SlugField(
        max_length=100,
    )
    color = ColorField(
        blank=True,
        default='',
    )
    description = models.CharField(
        max_length=200,
        blank=True,
    )

    class Meta:
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('parent', 'name'),
                name='%(app_label)s_%(class)s_parent_name',
            ),
            models.UniqueConstraint(
                fields=('name',),
                name='%(app_label)s_%(class)s_name',
                condition=models.Q(parent__isnull=True),
                violation_error_message='A top-level role with this name already exists.',
            ),
        )

    def __str__(self):
        return self.name

    def get_color(self):
        return self.color if self.color else None
