from rest_framework import serializers

from dcim.api.serializers import (
    CableSerializer,
    DeviceSerializer,
    DeviceTypeSerializer,
    LocationSerializer,
    ModuleSerializer,
    ModuleTypeSerializer,
    RackSerializer,
    RackTypeSerializer,
)
from netbox.api.serializers import (
    NestedGroupModelSerializer,
    NetBoxModelSerializer,
    PrimaryModelSerializer,
)
from tenancy.api.serializers import ContactSerializer, TenantSerializer

from ...choices import HardwareKindChoices
from ...models import Asset, AssetModuleEnd, AssetRole
from .nested import NestedAssetRoleSerializer

__all__ = (
    'AssetModuleEndSerializer',
    'AssetRoleSerializer',
    'AssetSerializer',
)


class AssetRoleSerializer(NestedGroupModelSerializer):
    parent = NestedAssetRoleSerializer(required=False, allow_null=True, default=None)
    asset_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = AssetRole
        fields = (
            'id',
            'url',
            'display_url',
            'display',
            'name',
            'slug',
            'parent',
            'color',
            'description',
            'owner',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
            'asset_count',
            '_depth',
        )
        brief_fields = (
            'id',
            'url',
            'display',
            'name',
            'slug',
            'description',
            'asset_count',
            '_depth',
        )


class AssetSerializer(PrimaryModelSerializer):
    # Read-only kind of hardware (device, module or rack), derived from the type
    kind = serializers.ChoiceField(choices=HardwareKindChoices, read_only=True)
    # Read-only: the module type has a cable assembly profile
    is_assembly = serializers.BooleanField(read_only=True)
    # Read-only: the cable of a cable assembly, managed by the plugin
    assembly_cable = CableSerializer(nested=True, read_only=True)
    device_type = DeviceTypeSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    device = DeviceSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    module_type = ModuleTypeSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    module = ModuleSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    rack_type = RackTypeSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    rack = RackSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    storage_location = LocationSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    tenant = TenantSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    contact = ContactSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    owning_tenant = TenantSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    role = AssetRoleSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if self.nested:
            # a related asset (e.g. of an assembly end) resolves to the instance
            return ret
        # store empty asset tag and serial as NULL, so that the unique
        # constraints ignore them
        if 'asset_tag' in ret and ret['asset_tag'] == '':
            ret['asset_tag'] = None
        if 'serial' in ret and ret['serial'] == '':
            ret['serial'] = None
        return ret

    class Meta:
        model = Asset
        fields = (
            'id',
            'url',
            'display_url',
            'display',
            'name',
            'description',
            'asset_tag',
            'serial',
            'status',
            'kind',
            'is_assembly',
            'assembly_cable',
            'role',
            'device_type',
            'device',
            'module_type',
            'module',
            'rack_type',
            'rack',
            'tenant',
            'contact',
            'storage_location',
            'owning_tenant',
            'owner',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = (
            'id',
            'url',
            'display',
            'serial',
            'name',
            'description',
        )
        # DRF automatically creates validators from the model's unique
        # constraints. They don't work when some fields of a constraint may be
        # NULL, so we remove them and rely on the model's validation instead.
        # See https://www.django-rest-framework.org/api-guide/validators/#optional-fields
        validators = []


class AssetModuleEndSerializer(NetBoxModelSerializer):
    asset = AssetSerializer(nested=True)
    module = ModuleSerializer(nested=True)
    label = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=AssetModuleEnd._meta.get_field('label').max_length,
        help_text=AssetModuleEnd._meta.get_field('label').help_text,
    )
    side = serializers.CharField(read_only=True)

    class Meta:
        model = AssetModuleEnd
        fields = (
            'id',
            'url',
            'display_url',
            'display',
            'asset',
            'module',
            'label',
            'side',
            'is_primary',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = (
            'id',
            'url',
            'display',
            'label',
            'is_primary',
        )
        # The "one primary end" constraint is handled by the model (the old
        # primary end is unset on save), so DRF must not validate it
        validators = []
