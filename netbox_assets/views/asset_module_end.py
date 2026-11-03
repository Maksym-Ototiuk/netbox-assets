from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect

from extras.ui.panels import CustomFieldsPanel, TagsPanel
from netbox.ui import attrs, layout, panels
from netbox.views import generic
from netbox.views.generic.base import BaseObjectView
from utilities.views import GetReturnURLMixin, register_model_view

from .. import filtersets, forms, models, tables

__all__ = (
    'AssetModuleEndView',
    'AssetModuleEndListView',
    'AssetModuleEndEditView',
    'AssetModuleEndDeleteView',
    'AssetModuleEndSetPrimaryView',
    'AssetModuleEndBulkImportView',
    'AssetModuleEndBulkDeleteView',
)


class AssetModuleEndPanel(panels.ObjectAttributesPanel):
    asset = attrs.RelatedObjectAttr('asset', linkify=True, label='Cable assembly')
    label = attrs.TextAttr('label', label='End')
    side = attrs.TextAttr('side')
    is_primary = attrs.BooleanAttr('is_primary', label='Primary')
    device = attrs.RelatedObjectAttr('module.device', linkify=True, label='Device')
    module_bay = attrs.RelatedObjectAttr(
        'module.module_bay', linkify=True, label='Module bay'
    )
    module = attrs.RelatedObjectAttr('module', linkify=True)
    module_type = attrs.RelatedObjectAttr(
        'module.module_type', linkify=True, label='Module type'
    )


@register_model_view(models.AssetModuleEnd)
class AssetModuleEndView(generic.ObjectView):
    queryset = models.AssetModuleEnd.objects.select_related(
        'asset__module_type__profile',
        'module__device',
        'module__module_bay',
        'module__module_type',
    )
    layout = layout.SimpleLayout(
        left_panels=[
            AssetModuleEndPanel(),
        ],
        right_panels=[
            TagsPanel(),
            CustomFieldsPanel(),
        ],
        bottom_panels=[
            panels.ObjectsTablePanel(
                model='dcim.Interface',
                title='Interfaces',
                filters={'module_id': lambda ctx: ctx['object'].module_id},
            ),
        ],
    )


@register_model_view(models.AssetModuleEnd, 'list', path='', detail=False)
class AssetModuleEndListView(generic.ObjectListView):
    queryset = models.AssetModuleEnd.objects.select_related(
        'asset__module_type__manufacturer',
        'asset__module_type__profile',
        'module__device',
        'module__module_bay',
        'module__module_type__manufacturer',
    )
    table = tables.AssetModuleEndTable
    filterset = filtersets.AssetModuleEndFilterSet
    filterset_form = forms.AssetModuleEndFilterForm


@register_model_view(models.AssetModuleEnd, 'add', detail=False)
@register_model_view(models.AssetModuleEnd, 'edit')
class AssetModuleEndEditView(generic.ObjectEditView):
    queryset = models.AssetModuleEnd.objects.all()
    form = forms.AssetModuleEndForm


@register_model_view(models.AssetModuleEnd, 'delete')
class AssetModuleEndDeleteView(generic.ObjectDeleteView):
    """Uninstall an end. The module stays in NetBox."""

    queryset = models.AssetModuleEnd.objects.all()


@register_model_view(models.AssetModuleEnd, 'set_primary', path='set-primary')
class AssetModuleEndSetPrimaryView(GetReturnURLMixin, BaseObjectView):
    """Make an end the primary end of its cable assembly."""

    queryset = models.AssetModuleEnd.objects.all()

    def get_required_permission(self):
        return 'netbox_assets.change_assetmoduleend'

    def get(self, request, pk):
        end = get_object_or_404(self.queryset, pk=pk)
        return redirect(end.get_absolute_url())

    def post(self, request, pk):
        end = get_object_or_404(self.queryset, pk=pk)
        end.snapshot()
        end.is_primary = True
        try:
            end.full_clean()
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
        else:
            end.save()
            messages.success(
                request, f'{end.label} is now the primary end of {end.asset}.'
            )
        return redirect(self.get_return_url(request, end.asset))


@register_model_view(models.AssetModuleEnd, 'bulk_import', path='import', detail=False)
class AssetModuleEndBulkImportView(generic.BulkImportView):
    queryset = models.AssetModuleEnd.objects.all()
    model_form = forms.AssetModuleEndImportForm


@register_model_view(models.AssetModuleEnd, 'bulk_delete', path='delete', detail=False)
class AssetModuleEndBulkDeleteView(generic.BulkDeleteView):
    queryset = models.AssetModuleEnd.objects.all()
    filterset = filtersets.AssetModuleEndFilterSet
    table = tables.AssetModuleEndTable
