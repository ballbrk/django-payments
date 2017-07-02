
from django import forms

class IBANBankingForm(forms.Form):
    # only shown, return is ignored
    orderid = forms.CharField(disabled=True)
    iban = forms.CharField(disabled=True)
    bic = forms.CharField(disabled=True)
