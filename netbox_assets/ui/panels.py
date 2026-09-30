from django.db.models import Count

from netbox.ui import attrs, panels

from ..choices import AssetStatusChoices
from ..models import Asset

__all__ = (
    'AssetRolePanel',
    'AssetRoleStatusPanel',
)


class AssetRolePanel(panels.NestedGroupObjectPanel):
    color = attrs.ColorAttr('color')


class AssetRoleStatusPanel(panels.Panel):
    """
    Number of assets per status for an asset role, including assets of all
    child roles.
    """

    template_name = 'netbox_assets/inc/assetrole_status.html'
    title = 'Assets by status'

    def get_context(self, context):
        ctx = super().get_context(context)
        role = ctx['object']
        assets = Asset.objects.restrict(ctx['request'].user, 'view').filter(
            role__in=role.get_descendants(include_self=True)
        )
        counts = dict(
            assets.order_by().values_list('status').annotate(count=Count('pk'))
        )
        ctx['status_counts'] = [
            {
                'value': value,
                'label': label,
                'color': AssetStatusChoices.colors.get(value),
                'count': counts[value],
            }
            for value, label in AssetStatusChoices
            if counts.get(value)
        ]
        return ctx
