import strawberry
import strawberry_django

from .types import AssetRoleType, AssetType

__all__ = ('NetBoxAssetsQuery',)


# The name "Query" is required (as in NetBox core): strawberry-django adds the
# `id` argument to single-object fields only on a type named "Query". NetBox
# merges this class into its root Query type.
@strawberry.type(name='Query')
class NetBoxAssetsQuery:
    # As in NetBox core, results are restricted to objects the user is
    # permitted to view.
    asset: AssetType = strawberry_django.field()
    asset_list: list[AssetType] = strawberry_django.field()

    asset_role: AssetRoleType = strawberry_django.field()
    asset_role_list: list[AssetRoleType] = strawberry_django.field()
