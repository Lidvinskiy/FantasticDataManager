from django import forms
from django.forms import TextInput, PasswordInput


class LoginForm(forms.Form):
    login = forms.CharField(required=True, widget=TextInput(attrs={'class': 'form-control'}))
    key = forms.CharField(required=True, widget=PasswordInput(attrs={'class': 'form-control'}))
