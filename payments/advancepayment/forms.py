
from django import forms

class IBANBankingForm(forms.Form):
    # only shown, return is ignored
    orderid = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}))
    iban = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}))
    bic = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}))
    method="POST"

    def __init__(self, instance, payment, provider, *args, **kwargs):
        super(IBANBankingForm, self).__init__(instance, *args, **kwargs)
        self.payment = payment
        self.provider = provider
        self.action = ""
