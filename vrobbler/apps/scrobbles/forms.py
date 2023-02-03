from django import forms

from scrobbles.models import AudioScrobblerTSVImport


class UploadAudioscrobblerFileForm(forms.ModelForm):
    class Meta:
        model = AudioScrobblerTSVImport
        fields = ('tsv_file',)


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
