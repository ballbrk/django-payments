
from django import forms
from django.forms import widgets

 class IBANBankingForm(forms.Form):
     # only shown, return is ignored
     token = forms.Charfield(disabled=True)
     iban = forms.Charfield(disabled=True)
     bic = forms.Charfield(disabled=True)
