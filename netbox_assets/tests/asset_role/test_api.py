from utilities.testing import APIViewTestCases

from ...models import AssetRole
from ..custom import APITestCase


class AssetRoleTest(
    APITestCase,
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    model = AssetRole
    brief_fields = ['_depth', 'description', 'display', 'id', 'name', 'url']
    create_data = [
        {
            'name': 'Asset Role 4',
            'slug': 'asset-role-4',
        },
        {
            'name': 'Asset Role 5',
            'slug': 'asset-role-5',
        },
        {
            'name': 'Asset Role 6',
            'slug': 'asset-role-6',
        },
    ]
    bulk_update_data = {
        'description': 'new description',
    }

    @classmethod
    def setUpTestData(cls) -> None:
        AssetRole.objects.create(name='Asset Role 1', slug='asset-role-1')
        AssetRole.objects.create(name='Asset Role 2', slug='asset-role-2')
        AssetRole.objects.create(name='Asset Role 3', slug='asset-role-3')
