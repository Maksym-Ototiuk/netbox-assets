from typing import Annotated

import strawberry
import strawberry_django
from strawberry import ID
from strawberry_django import StrFilterLookup

from netbox.graphql.filters import NestedGroupModelFilter, PrimaryModelFilter

from .. import models

__all__ = (
    'AssetFilter',
    'AssetRoleFilter',
)


@strawberry_django.filter_type(models.AssetRole, lookups=True)
class AssetRoleFilter(NestedGroupModelFilter):
    color: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter_type(models.Asset, lookups=True)
class AssetFilter(PrimaryModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field()
    asset_tag: StrFilterLookup | None = strawberry_django.filter_field()
    serial: StrFilterLookup | None = strawberry_django.filter_field()
    status: StrFilterLookup | None = strawberry_django.filter_field()
    role: (
        Annotated['AssetRoleFilter', strawberry.lazy('netbox_assets.graphql.filters')]
        | None
    ) = strawberry_django.filter_field()
    role_id: ID | None = strawberry_django.filter_field()
    device_type_id: ID | None = strawberry_django.filter_field()
    module_type_id: ID | None = strawberry_django.filter_field()
    rack_type_id: ID | None = strawberry_django.filter_field()
    device_id: ID | None = strawberry_django.filter_field()
    module_id: ID | None = strawberry_django.filter_field()
    rack_id: ID | None = strawberry_django.filter_field()
    tenant_id: ID | None = strawberry_django.filter_field()
    contact_id: ID | None = strawberry_django.filter_field()
    owning_tenant_id: ID | None = strawberry_django.filter_field()
    storage_location_id: ID | None = strawberry_django.filter_field()
