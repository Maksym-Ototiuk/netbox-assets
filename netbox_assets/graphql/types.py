from typing import TYPE_CHECKING, Annotated

import strawberry
import strawberry_django

from extras.graphql.mixins import ImageAttachmentsMixin
from netbox.graphql.types import NestedLtreeGroupObjectType, PrimaryObjectType

from .. import models
from .filters import AssetFilter, AssetRoleFilter

if TYPE_CHECKING:
    # Only for type checkers and linters; at runtime the core types are
    # resolved lazily via strawberry.lazy()
    from dcim.graphql.types import (
        DeviceType,
        DeviceTypeType,
        LocationType,
        ModuleType,
        ModuleTypeType,
        RackType,
        RackTypeType,
    )
    from tenancy.graphql.types import ContactType, TenantType

__all__ = (
    'AssetRoleType',
    'AssetType',
)


@strawberry_django.type(
    models.AssetRole,
    # ltree internals are not exposed, the same as for DeviceRole in NetBox core;
    # the tree depth is available as the `level` field
    exclude=['path', 'sort_path'],
    filters=AssetRoleFilter,
    pagination=True,
)
class AssetRoleType(NestedLtreeGroupObjectType):
    parent: (
        Annotated['AssetRoleType', strawberry.lazy('netbox_assets.graphql.types')]
        | None
    )
    children: list[
        Annotated['AssetRoleType', strawberry.lazy('netbox_assets.graphql.types')]
    ]
    assets: list[Annotated['AssetType', strawberry.lazy('netbox_assets.graphql.types')]]
    color: str


@strawberry_django.type(
    models.Asset,
    fields='__all__',
    filters=AssetFilter,
    pagination=True,
)
class AssetType(ImageAttachmentsMixin, PrimaryObjectType):
    role: (
        Annotated['AssetRoleType', strawberry.lazy('netbox_assets.graphql.types')]
        | None
    )
    device_type: (
        Annotated['DeviceTypeType', strawberry.lazy('dcim.graphql.types')] | None
    )
    module_type: (
        Annotated['ModuleTypeType', strawberry.lazy('dcim.graphql.types')] | None
    )
    rack_type: Annotated['RackTypeType', strawberry.lazy('dcim.graphql.types')] | None
    device: Annotated['DeviceType', strawberry.lazy('dcim.graphql.types')] | None
    module: Annotated['ModuleType', strawberry.lazy('dcim.graphql.types')] | None
    rack: Annotated['RackType', strawberry.lazy('dcim.graphql.types')] | None
    tenant: Annotated['TenantType', strawberry.lazy('tenancy.graphql.types')] | None
    contact: Annotated['ContactType', strawberry.lazy('tenancy.graphql.types')] | None
    owning_tenant: (
        Annotated['TenantType', strawberry.lazy('tenancy.graphql.types')] | None
    )
    storage_location: (
        Annotated['LocationType', strawberry.lazy('dcim.graphql.types')] | None
    )
