
from django import forms
from localflavor.generic.forms import IBANFormField, BICFormField

 class IBANBankingForm(forms.Form):
     iban = IBANFormField()
     bic = BICFormField()
