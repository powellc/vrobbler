from django import forms


class ImdbScrobbleForm(forms.Form):
    imdb_id = forms.CharField(label="IMDB", max_length=30)
