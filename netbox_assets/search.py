from netbox.search import SearchIndex

from .models import Asset, AssetRole


class AssetIndex(SearchIndex):
    model = Asset
    fields = (
        ('name', 100),
        ('asset_tag', 50),
        ('serial', 60),
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('name', 'asset_tag', 'status')


class AssetRoleIndex(SearchIndex):
    model = AssetRole
    fields = (
        ('name', 100),
        ('slug', 110),
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('description',)


indexes = [
    AssetIndex,
    AssetRoleIndex,
]
