from django import forms


class ImdbScrobbleForm(forms.Form):
    imdb_id = forms.CharField(
        label="",
        widget=forms.TextInput(
            attrs={
                'class': "form-control form-control-dark w-100",
                'placeholder': "Scrobble something (IMDB ID, String, TVDB ID ...)",
                'aria-label': "Scrobble something",
            }
        ),
    )
