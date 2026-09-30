from rest_framework import serializers

from dcim.api.serializers import (
    DeviceSerializer,
    DeviceTypeSerializer,
    LocationSerializer,
    ModuleSerializer,
    ModuleTypeSerializer,
    RackSerializer,
    RackTypeSerializer,
)
from netbox.api.serializers import NestedGroupModelSerializer, PrimaryModelSerializer
from tenancy.api.serializers import ContactSerializer, TenantSerializer

from ...choices import HardwareKindChoices
from ...models import Asset, AssetRole
from .nested import NestedAssetRoleSerializer

__all__ = (
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
