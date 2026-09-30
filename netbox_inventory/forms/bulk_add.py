from django import forms

from utilities.forms.fields import ExpandableNameField

from .models import AssetForm

__all__ = (
    'AssetBulkAddForm',
    'AssetBulkAddModelForm',
)


class AssetBulkAddForm(forms.Form):
    """Form for creating multiple Assets by count"""

    count = forms.IntegerField(
        min_value=1,
        required=True,
        help_text='How many assets to create',
    )
    pattern = ExpandableNameField(
        label='Asset tag pattern',
        required=False,
        help_text='Optional. Supports alphanumeric ranges and must expand to the same number as count.',
    )

    def clean(self):
        cleaned_data = super().clean()
        count = cleaned_data.get('count')
        pattern = cleaned_data.get('pattern')

        if count and pattern and len(pattern) != count:
            self.add_error(
                'pattern',
                f'Pattern expands to {len(pattern)} values, but count is {count}.',
            )

        return cleaned_data


class AssetBulkAddModelForm(AssetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset_tag'].disabled = True
        self.fields['serial'].disabled = True
