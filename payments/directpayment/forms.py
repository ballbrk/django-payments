from django import forms

class OrderForm(forms.Form):
    # only shown, return is ignored
    orderid = forms.CharField(disabled=True)
    extracosts = forms.CharField(disabled=True)
    method = "POST"

    def __init__(self, instance, payment, provider, extracosts=0, *args, **kwargs):
        super(OrderForm, self).__init__(instance, *args, extracosts=extracosts, **kwargs)
        if instance and extracosts==0:
            del self.fields['extracosts']
        self.payment = payment
        self.provider = provider
        self.action = ""
