from django import forms


class ExportScrobbleForm(forms.Form):
    """Provide options for downloading scrobbles"""

    EXPORT_TYPES = (
        ('as', 'Audioscrobbler'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
    )
    export_type = forms.ChoiceField(choices=EXPORT_TYPES)


class ScrobbleForm(forms.Form):
    item_id = forms.CharField(
        label="",
        widget=forms.TextInput(
            attrs={
                'class': "form-control form-control-dark w-100",
                'placeholder': "Scrobble something (IMDB ID, String, TVDB ID ...)",
                'aria-label': "Scrobble something",
            }
        ),
    )
