from netbox.api.serializers import WritableNestedSerializer

from ...models import AssetRole

__all__ = ('NestedAssetRoleSerializer',)


class NestedAssetRoleSerializer(WritableNestedSerializer):
    """
    Used only for the self-referencing `parent` field of AssetRoleSerializer,
    the same way as NestedDeviceRoleSerializer in NetBox core.
    """

    class Meta:
        model = AssetRole
        fields = ('id', 'url', 'display_url', 'display', 'name')
