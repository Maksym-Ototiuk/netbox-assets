from utilities.testing import APIViewTestCases

from netbox_assets.models import AssetRole
from netbox_assets.tests.custom import APITestCase


class AssetRoleTest(APITestCase, APIViewTestCases.APIViewTestCase):
    """
    REST API and GraphQL tests for asset roles
    """

    model = AssetRole
    brief_fields = [
        '_depth',
        'asset_count',
        'description',
        'display',
        'id',
        'name',
        'slug',
        'url',
    ]
    bulk_update_data = {
        'description': 'New description',
    }
    bulk_update_invalid_data = {
        'name': '',
    }

    @classmethod
    def setUpTestData(cls):
        role1 = AssetRole.objects.create(
            name='Asset Role 1', slug='asset-role-1', color='ff0000'
        )
        AssetRole.objects.create(
            name='Asset Role 2', slug='asset-role-2', color='00ff00'
        )
        AssetRole.objects.create(
            name='Asset Role 3', slug='asset-role-3', color='0000ff'
        )

        cls.create_data = [
            {
                'name': 'Asset Role 4',
                'slug': 'asset-role-4',
                'color': 'ffff00',
            },
            {
                'name': 'Asset Role 5',
                'slug': 'asset-role-5',
                'parent': role1.pk,
            },
            {
                'name': 'Asset Role 6',
                'slug': 'asset-role-6',
                'parent': role1.pk,
            },
        ]
