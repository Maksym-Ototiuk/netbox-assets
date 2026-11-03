from django.contrib import messages
from django.shortcuts import redirect

from netbox.views import generic

from ..forms.assign import *
from ..models import Asset

__all__ = ('AssetAssignView',)


class AssetAssignView(generic.ObjectEditView):
    queryset = Asset.objects.all()
    template_name = 'netbox_assets/asset_assign.html'

    def dispatch(self, request, *args, **kwargs):
        # Set the form class based on the type of hardware being assigned
        obj = self.get_object(**kwargs)
        if obj.is_assembly:
            messages.info(request, 'A cable assembly is installed through its ends.')
            return redirect(obj.get_absolute_url() + '#assembly-ends')
        self.form = {
            'device': AssetDeviceAssignForm,
            'module': AssetModuleAssignForm,
            'rack': AssetRackAssignForm,
        }[obj.kind]
        return super().dispatch(request, *args, **kwargs)
