from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Location, Module, Rack, Site
from netbox.forms import NetBoxModelForm
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.rendering import FieldSet

from ..choices import AssetStatusChoices
from ..models import Asset
from ..utils import get_status_for

__all__ = (
    'AssetDeviceReassignForm',
    'AssetModuleReassignForm',
    'AssetRackReassignForm',
)


class AssetReassignMixin(forms.Form):
    storage_site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
        help_text='Limit New Asset choices only to assets stored at this site',
    )
    storage_location = DynamicModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        query_params={
            'site_id': '$storage_site',
        },
        help_text='Limit New Asset choices only to assets stored at this location',
    )
    asset_status = forms.ChoiceField(
        choices=AssetStatusChoices,
        initial=get_status_for('stored'),
        label='Status',
        help_text='Status to set to existing asset that is being unassigned',
    )
    old_storage_site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label='Storage site for old Asset',
        help_text='Limit Storage location choices for old Asset to this site',
    )
    old_storage_location = DynamicModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        query_params={
            'site_id': '$old_storage_site',
        },
        label='Storage location for old Asset',
        help_text='Where the old Asset will be stored. Prefilled with the current '
        'location of the hardware. Leave empty to save without a location',
    )

    fieldsets = (
        FieldSet(
            'storage_site', 'storage_location', 'assigned_asset', name=_('New Asset')
        ),
        FieldSet(
            'old_storage_site',
            'old_storage_location',
            'asset_status',
            name=_('Old Asset'),
        ),
    )

    class Meta:
        fields = (
            'storage_site',
            'storage_location',
            'assigned_asset',
            'old_storage_site',
            'old_storage_location',
            'asset_status',
        )

    def save(self, commit=True):
        # if existing assigned_asset, clear assignment before save
        # handle snapshot for old and new asset
        """
        Save this form's self.instance object if commit=True. Otherwise, add
        a save_m2m() method to the form which can be called after the instance
        is saved manually at a later time. Return the model instance.
        """
        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate."
                % (
                    self.instance._meta.object_name,
                    'created' if self.instance._state.adding else 'changed',
                )
            )
        if commit:
            self.instance.snapshot()
            if self.old_asset:
                self.old_asset.status = self.cleaned_data['asset_status']
                # if assigning another asset, don't clear data from device object
                # will overwrite via new_asset.save later
                # this is to avoid creating two changelog entries for device
                self.old_asset.save(clear_old_hw=not bool(self.new_asset))
            if self.new_asset:
                self.new_asset.save()
        return self.instance

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        if self.errors:
            return cleaned_data
        try:
            self.old_asset = self.instance.assigned_asset
        except Asset.DoesNotExist:
            # no asset currently assigned
            self.old_asset = None
        self.new_asset = self.cleaned_data['assigned_asset']
        if self.old_asset == self.new_asset:
            raise ValidationError(
                'Cannot reasign the same asset as is already assigned'
            )
        old_storage_site = self.cleaned_data.get('old_storage_site')
        old_storage_location = self.cleaned_data.get('old_storage_location')
        # the location dropdown is filtered by site only in the browser,
        # so check that the location belongs to the site here as well
        if (
            old_storage_site
            and old_storage_location
            and old_storage_location.site_id != old_storage_site.pk
        ):
            raise ValidationError(
                {
                    'old_storage_location': 'Storage location for old Asset must '
                    'belong to Storage site for old Asset'
                }
            )
        # set device/module for asset and clean/validate
        if self.old_asset:
            # empty location means the old asset is stored without a location
            self._clean_asset(
                self.old_asset, None, storage_location=old_storage_location
            )
        if self.new_asset:
            self._clean_asset(self.new_asset, self.instance)
        return cleaned_data

    def _clean_asset(self, asset, instance, **changes):
        # store old state of asset objects for changelog
        # (must be done before any field of the asset is changed)
        asset.snapshot()
        try:
            # update hardware assignment and validate data
            setattr(asset, asset.kind, instance)
            # other field changes, e.g. storage_location for the old asset
            for field_name, value in changes.items():
                setattr(asset, field_name, value)
            # signal to assset.clean() methods to not validate _type match beetween asset and hw
            asset._in_reassign = True
            asset.full_clean(exclude=(asset.kind,))
        except ValidationError as e:
            # ValidationError raised for device or module field
            # "remap" to error for whole form
            raise ValidationError(e.messages)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # remove tags field from form
        self.fields.pop('tags')

        # Remove Custom Fields from form
        for cf_name in self.custom_fields.keys():
            self.fields.pop(cf_name, None)
        self.custom_fields = {}
        self.custom_fields_groups = {}

        try:
            old_asset = self.instance.assigned_asset
        except Asset.DoesNotExist:
            # no asset currently assigned, hide fields for old asset
            self.fields.pop('asset_status')
            self.fields.pop('old_storage_site')
            self.fields.pop('old_storage_location')
            self.fieldsets = (self.fieldsets[0],)
        else:
            # prefill storage of old asset with the place where the hardware
            # is installed now, so it stays there if the user changes nothing
            # (values from the URL query string take precedence)
            site = old_asset.installed_site
            location = old_asset.installed_location
            self.initial.setdefault('old_storage_site', site.pk if site else None)
            self.initial.setdefault(
                'old_storage_location', location.pk if location else None
            )

class AssetDeviceReassignForm(AssetReassignMixin, NetBoxModelForm):
    assigned_asset = DynamicModelChoiceField(
        queryset=Asset.objects.filter(device_type__isnull=False, device__isnull=True),
        required=False,
        selector=True,
        query_params={
            'kind': 'device',
            'is_assigned': False,
            'storage_site_id': '$storage_site',
            'storage_location_id': '$storage_location',
        },
        label='New Asset',
        help_text='New asset to assign to device',
    )

    class Meta:
        model = Device
        fields = AssetReassignMixin.Meta.fields


class AssetModuleReassignForm(AssetReassignMixin, NetBoxModelForm):
    assigned_asset = DynamicModelChoiceField(
        queryset=Asset.objects.filter(module_type__isnull=False, module__isnull=True),
        required=False,
        selector=True,
        query_params={
            'kind': 'module',
            'is_assigned': False,
            'storage_site_id': '$storage_site',
            'storage_location_id': '$storage_location',
        },
        label='New Asset',
        help_text='New asset to assign to module',
    )

    class Meta:
        model = Module
        fields = AssetReassignMixin.Meta.fields


class AssetRackReassignForm(AssetReassignMixin, NetBoxModelForm):
    assigned_asset = DynamicModelChoiceField(
        queryset=Asset.objects.filter(rack_type__isnull=False, rack__isnull=True),
        required=False,
        selector=True,
        query_params={
            'kind': 'rack',
            'is_assigned': False,
            'storage_site_id': '$storage_site',
            'storage_location_id': '$storage_location',
        },
        label='New Asset',
        help_text='New asset to assign to rack',
    )

    class Meta:
        model = Rack
        fields = AssetReassignMixin.Meta.fields
