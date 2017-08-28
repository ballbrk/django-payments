from django.utils.translation import ugettext_lazy as _
from django import forms

class IBANBankingForm(forms.Form):
    # only shown, return is ignored
    iban = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}), label="IBAN")
    bic = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}), label="BIC")
    order = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}), label=_("Please supply as reference"))
    method = "post"
    action = ""

    def __init__(self, instance, payment, provider, *args, **kwargs):
        super(IBANBankingForm, self).__init__(instance, *args, **kwargs)
        self.payment = payment
        self.provider = provider
        #self.action = provider.get_return_url(payment)
