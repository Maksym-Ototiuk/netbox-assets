from dcim.models import Device, Module, Rack
from netbox.views import generic

from ..forms.reassign import *

__all__ = (
    'AssetDeviceReassignView',
    'AssetModuleReassignView',
    'AssetRackReassignView',
)


class AssetDeviceReassignView(generic.ObjectEditView):
    queryset = Device.objects.all()
    template_name = 'netbox_assets/asset_reassign.html'
    form = AssetDeviceReassignForm


class AssetModuleReassignView(generic.ObjectEditView):
    queryset = Module.objects.all()
    template_name = 'netbox_assets/asset_reassign.html'
    form = AssetModuleReassignForm


class AssetRackReassignView(generic.ObjectEditView):
    queryset = Rack.objects.all()
    template_name = 'netbox_assets/asset_reassign.html'
    form = AssetRackReassignForm
