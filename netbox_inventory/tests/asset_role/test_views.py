from utilities.testing import ViewTestCases

from netbox_inventory.models import AssetRole
from netbox_inventory.tests.custom import ModelViewTestCase


class AssetRoleTestCase(
    ModelViewTestCase,
    ViewTestCases.PrimaryObjectViewTestCase,
):
    model = AssetRole

    form_data = {
        'name': 'Asset Role',
        'slug': 'asset-role',
        'description': 'asset role description',
    }
    csv_data = (
        'name,slug',
        'Asset Role 4,asset-role-4',
        'Asset Role 5,asset-role-5',
        'Asset Role 6,asset-role-6',
    )
    bulk_edit_data = {
        'description': 'bulk description',
    }

    @classmethod
    def setUpTestData(cls):
        role1 = AssetRole.objects.create(
            name='Asset Role 1',
            slug='asset-role-1',
        )
        role2 = AssetRole.objects.create(
            name='Asset Role 2',
            slug='asset-role-2',
        )
        role3 = AssetRole.objects.create(
            name='Asset Role 3',
            slug='asset-role-3',
        )
        cls.csv_update_data = (
            'id,description',
            f'{role1.pk},description 1',
            f'{role2.pk},description 2',
            f'{role3.pk},description 3',
        )
