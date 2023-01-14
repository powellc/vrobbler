from django import forms


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
