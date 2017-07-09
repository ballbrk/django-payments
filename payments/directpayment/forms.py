
from django import forms

class OrderIdForm(forms.Form):
    # only shown, return is ignored
    orderid = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}))
    method = "post"
    action = ""

    def __init__(self, instance, payment, provider, *args, **kwargs):
        super(OrderIdForm, self).__init__(instance, *args, **kwargs)
        self.payment = payment
        self.provider = provider
