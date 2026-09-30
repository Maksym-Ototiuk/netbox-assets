from django.utils.translation import gettext_lazy as _

from extras.ui.panels import CustomFieldsPanel, TagsPanel
from netbox.ui import actions, layout
from netbox.ui.breadcrumbs import Breadcrumb, filtered_list_url
from netbox.ui.panels import CommentsPanel, ObjectsTablePanel, RelatedObjectsPanel
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


@register_model_view(models.AssetRole, 'list', path='', detail=False)
class AssetRoleListView(generic.ObjectListView):
    # Asset counts include assets of all child roles (cumulative=True)
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


@register_model_view(models.AssetRole)
class AssetRoleView(GetRelatedModelsMixin, generic.ObjectView):
    queryset = models.AssetRole.objects.all()
    layout = layout.SimpleLayout(
        # Breadcrumbs (NetBox 4.7): one crumb per ancestor role, each linking to
        # the list of its child roles
        breadcrumbs=[
            Breadcrumb(
                lambda o: o.get_ancestors(),
                url=filtered_list_url(
                    'plugins:netbox_assets:assetrole_list', 'parent_id'
                ),
            ),
        ],
        left_panels=[
            AssetRolePanel(),
            TagsPanel(),
        ],
        right_panels=[
            AssetRoleStatusPanel(),
            RelatedObjectsPanel(),
            CustomFieldsPanel(),
            CommentsPanel(),
        ],
        bottom_panels=[
            ObjectsTablePanel(
                model='netbox_assets.AssetRole',
                title=_('Child Asset Roles'),
                filters={'parent_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['parent'],
                actions=[
                    actions.AddObject(
                        'netbox_assets.AssetRole',
                        url_params={'parent': lambda ctx: ctx['object'].pk},
                    ),
                ],
            ),
        ],
    )

    def get_extra_context(self, request, instance):
        return {
            'related_models': self.get_related_models(request, instance),
        }


@register_model_view(models.AssetRole, 'add', detail=False)
@register_model_view(models.AssetRole, 'edit')
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
    queryset = models.AssetRole.objects.add_related_count(
        models.AssetRole.objects.all(),
        models.Asset,
        'role',
        'asset_count',
        cumulative=True,
    )
    filterset = filtersets.AssetRoleFilterSet
    table = tables.AssetRoleTable
    form = forms.AssetRoleBulkEditForm


@register_model_view(models.AssetRole, 'bulk_delete', path='delete', detail=False)
class AssetRoleBulkDeleteView(generic.BulkDeleteView):
    queryset = models.AssetRole.objects.add_related_count(
        models.AssetRole.objects.all(),
        models.Asset,
        'role',
        'asset_count',
        cumulative=True,
    )
    filterset = filtersets.AssetRoleFilterSet
    table = tables.AssetRoleTable
