from django.contrib.postgres.indexes import GistIndex
from django.db import models
from django.utils.translation import gettext_lazy as _

from netbox.models import NestedLtreeGroupModel
from utilities.fields import ColorField

__all__ = ('AssetRole',)


class AssetRole(NestedLtreeGroupModel):
    """
    Functional role of an Asset (e.g. Router, Switch, SFP, Line Card).

    Roles can be nested. The tree is stored in a PostgreSQL ltree column
    (`path`) that is maintained by database triggers, the same way as
    DeviceRole in NetBox core. The triggers are installed by the
    InstallLtreeTriggers operation in the initial migration.
    """

    color = ColorField(
        verbose_name=_('color'),
        blank=True,
        default='',
    )

    clone_fields = ('parent', 'description')

    class Meta:
        ordering = ('sort_path',)
        indexes = (
            GistIndex(fields=['path'], name='netbox_assets_role_path_gist'),
            models.Index(fields=['sort_path'], name='netbox_assets_role_sort_idx'),
        )
        constraints = (
            models.UniqueConstraint(
                fields=('parent', 'name'),
                name='%(app_label)s_%(class)s_parent_name',
                nulls_distinct=False,
                violation_error_message=_(
                    'An asset role with this name already exists.'
                ),
            ),
            models.UniqueConstraint(
                fields=('parent', 'slug'),
                name='%(app_label)s_%(class)s_parent_slug',
                nulls_distinct=False,
                violation_error_message=_(
                    'An asset role with this slug already exists.'
                ),
            ),
        )
        verbose_name = _('asset role')
        verbose_name_plural = _('asset roles')

    def get_color(self):
        return self.color or None
