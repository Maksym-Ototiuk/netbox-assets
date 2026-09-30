from rest_framework import serializers

from netbox.api.serializers import WritableNestedSerializer

from netbox_inventory.models import AssetRole, InventoryItemGroup

__all__ = (
    'NestedAssetRoleSerializer',
    'NestedInventoryItemGroupSerializer',
)


class NestedInventoryItemGroupSerializer(WritableNestedSerializer):
    _depth = serializers.IntegerField(source='level', read_only=True)

    class Meta:
        model = InventoryItemGroup
        fields = ('id', 'url', 'display', 'name', 'description', '_depth')

class NestedAssetRoleSerializer(WritableNestedSerializer):
    _depth = serializers.IntegerField(source='level', read_only=True)

    class Meta:
        model = AssetRole
        fields = ('id', 'url', 'display', 'name', 'description', '_depth')
