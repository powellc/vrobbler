from django import forms
from django.urls import reverse_lazy

class WebPageReadForm(forms.Form):
    notes = forms.CharField(widget=forms.Textarea, required=False)
    success_url = reverse_lazy("vrobbler-home")
