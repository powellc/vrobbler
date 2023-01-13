from django import forms


class ScrobbleForm(forms.Form):
    imdb_id = forms.CharField(label="IMDB", max_length=30)
