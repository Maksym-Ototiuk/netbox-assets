from utilities.testing import ViewTestCases, create_tags

from netbox_assets.models import AssetRole
from netbox_assets.tests.custom import ModelViewTestCase


class AssetRoleTestCase(
    ModelViewTestCase,
    ViewTestCases.OrganizationalObjectViewTestCase,
):
    """
    UI view tests for asset roles
    """

    model = AssetRole

    @classmethod
    def setUpTestData(cls):
        roles = [
            AssetRole.objects.create(name='Asset Role 1', slug='asset-role-1'),
            AssetRole.objects.create(name='Asset Role 2', slug='asset-role-2'),
            AssetRole.objects.create(name='Asset Role 3', slug='asset-role-3'),
            AssetRole.objects.create(name='Asset Role 4', slug='asset-role-4'),
        ]
        roles.append(
            AssetRole.objects.create(
                name='Asset Role 5', slug='asset-role-5', parent=roles[3]
            )
        )
        tags = create_tags('Alpha', 'Bravo', 'Charlie')

        cls.form_data = {
            'name': 'Asset Role X',
            'slug': 'asset-role-x',
            'color': 'c0c0c0',
            'description': 'New asset role',
            'tags': [t.pk for t in tags],
        }
        cls.csv_data = (
            'name,slug,parent,color',
            'Asset Role 6,asset-role-6,,ff0000',
            'Asset Role 7,asset-role-7,Asset Role 1,00ff00',
            'Asset Role 8,asset-role-8,Asset Role 1,0000ff',
        )
        cls.csv_update_data = (
            'id,name,description',
            f'{roles[0].pk},Asset Role 11,New description 11',
            f'{roles[1].pk},Asset Role 12,New description 12',
            f'{roles[2].pk},Asset Role 13,New description 13',
            f'{roles[4].pk},Asset Role 15,New description 15',
        )
        cls.bulk_edit_data = {
            'color': '00ff00',
            'description': 'New description',
        }
