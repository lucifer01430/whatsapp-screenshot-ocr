from django import forms

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class UploadForm(forms.Form):
    images = forms.FileField(
        widget=MultiFileInput(),
        required=True
    )
