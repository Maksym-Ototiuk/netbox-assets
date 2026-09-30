from netbox.ui import attrs, panels

from netbox_inventory.choices import AssetStatusChoices
from netbox_inventory.models import Asset


class AssetRolePanel(panels.NestedGroupObjectPanel):
    color = attrs.ColorAttr('color')


class AssetRoleStatusPanel(panels.Panel):
    template_name = 'netbox_inventory/inc/assetrole_status.html'

    def get_context(self, context):
        ctx = super().get_context(context)
        instance = context.get('object')
        request = context.get('request')
        assets = Asset.objects.restrict(request.user, 'view').filter(
            role__in=instance.get_descendants(include_self=True)
        )
        status_counts = {
            key: {
                'value': key,
                'label': label,
                'color': AssetStatusChoices.colors[key],
                'count': assets.filter(status=key).count(),
            }
            for key, label in list(AssetStatusChoices)
        }
        ctx['status_counts'] = status_counts
        return ctx

def render(self, context):
        from django.template.loader import render_to_string
        request = context.get('request')
        if request is None:
            # fallback
            try:
                request = context['view'].request
            except (KeyError, AttributeError):
                pass
        ctx = self.get_context(context)
        return render_to_string(self.template_name, ctx, request=request)
