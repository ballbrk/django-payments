
from django import forms

class IBANBankingForm(forms.Form):
    # only shown, return is ignored
    orderid = forms.Charfield(disabled=True)
    iban = forms.Charfield(disabled=True)
    bic = forms.Charfield(disabled=True)
