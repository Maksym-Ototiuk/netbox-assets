from .schema import NetBoxAssetsQuery

# Loaded by NetBox as the plugin's GraphQL schema (PluginConfig resource
# 'graphql.schema'). The query fields are merged into NetBox's root Query.
schema = [
    NetBoxAssetsQuery,
]
