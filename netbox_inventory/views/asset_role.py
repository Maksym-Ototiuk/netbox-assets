from netbox.ui import actions, layout
from netbox.ui.panels import (
    CommentsPanel,
    ObjectsTablePanel,
)
from netbox.views import generic
from utilities.views import GetRelatedModelsMixin, register_model_view

from .. import filtersets, forms, models, tables
from ..ui.panels import AssetRolePanel, AssetRoleStatusPanel

__all__ = (
    'AssetRoleView',
    'AssetRoleListView',
    'AssetRoleEditView',
    'AssetRoleDeleteView',
    'AssetRoleBulkImportView',
    'AssetRoleBulkEditView',
    'AssetRoleBulkDeleteView',
)

@register_model_view(models.AssetRole)
class AssetRoleView(GetRelatedModelsMixin, generic.ObjectView):
    queryset = models.AssetRole.objects.all()
    layout = layout.SimpleLayout(
        left_panels=[
            AssetRolePanel(),
        ],
        right_panels=[
            AssetRoleStatusPanel(),
            CommentsPanel(),
        ],
        bottom_panels=[
            ObjectsTablePanel(
                model='netbox_inventory.AssetRole',
                title='Child Asset Roles',
                filters={'parent_id': lambda ctx: ctx['object'].pk},
                actions=[
                    actions.AddObject('netbox_inventory.AssetRole', url_params={'parent': lambda ctx: ctx['object'].pk}),
                ],
            ),
        ]
    )

    def get_extra_context(self, request, instance):
        from ..choices import AssetStatusChoices

        assets = models.Asset.objects.restrict(request.user, 'view').filter(
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

        return {
            'related_models': self.get_related_models(request, instance),
            'status_counts': status_counts,
            'asset_count': assets.count(),
        }


@register_model_view(models.AssetRole, 'list', path='', detail=False)
class AssetRoleListView(generic.ObjectListView):
    queryset = models.AssetRole.objects.add_related_count(
        models.AssetRole.objects.all(),
        models.Asset,
        'role',
        'asset_count',
        cumulative=True,
    )
    table = tables.AssetRoleTable
    filterset = filtersets.AssetRoleFilterSet
    filterset_form = forms.AssetRoleFilterForm


@register_model_view(models.AssetRole, 'edit')
@register_model_view(models.AssetRole, 'add', detail=False)
class AssetRoleEditView(generic.ObjectEditView):
    queryset = models.AssetRole.objects.all()
    form = forms.AssetRoleForm


@register_model_view(models.AssetRole, 'delete')
class AssetRoleDeleteView(generic.ObjectDeleteView):
    queryset = models.AssetRole.objects.all()


@register_model_view(models.AssetRole, 'bulk_import', path='import', detail=False)
class AssetRoleBulkImportView(generic.BulkImportView):
    queryset = models.AssetRole.objects.all()
    model_form = forms.AssetRoleImportForm


@register_model_view(models.AssetRole, 'bulk_edit', path='edit', detail=False)
class AssetRoleBulkEditView(generic.BulkEditView):
    queryset = models.AssetRole.objects.all()
    filterset = filtersets.AssetRoleFilterSet
    table = tables.AssetRoleTable
    form = forms.AssetRoleBulkEditForm


@register_model_view(models.AssetRole, 'bulk_delete', path='delete', detail=False)
class AssetRoleBulkDeleteView(generic.BulkDeleteView):
    queryset = models.AssetRole.objects.all()
    filterset = filtersets.AssetRoleFilterSet
    table = tables.AssetRoleTable
