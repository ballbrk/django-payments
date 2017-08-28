from django.utils.translation import ugettext_lazy as _
from django import forms

class OrderIdForm(forms.Form):
    # only shown, return is ignored
    order = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}), label=_("Please supply as reference"))
    method = "post"
    action = ""

    def __init__(self, instance, payment, provider, *args, **kwargs):
        super(OrderIdForm, self).__init__(instance, *args, **kwargs)
        self.payment = payment
        self.provider = provider
