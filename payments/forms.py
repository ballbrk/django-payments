from __future__ import unicode_literals

try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .fields import (CreditCardNumberField, CreditCardExpiryField,
                     CreditCardVerificationField, CreditCardNameField)
from .core import PAYMENT_VARIANTS_API


class SelectPaymentForm(forms.Form):
    """ Select a variant """
    variants = list(getattr(settings, 'PAYMENT_VARIANTS_API', PAYMENT_VARIANTS_API).keys())
    if getattr(settings, 'TRANSLATE_VARIANTS', False):
        variant = forms.ChoiceField(choices=map(lambda x: (x, _(x)), variants), required=True, label=_("Payment Method"))
    else:
        variant = forms.ChoiceField(choices=map(lambda x: (x, x), variants), required=True, label=_("Payment Method"))

class PaymentForm(forms.Form):
    '''
    Payment form, suitable for Django templates.

    When displaying the form remember to use *action* and *method*.
    '''
    def __init__(self, data=None, action='', method='post', provider=None,
                 payment=None, hidden_inputs=True, autosubmit=False):
        if hidden_inputs and data is not None:
            super(PaymentForm, self).__init__(auto_id=False)
            for key, val in data.items():
                widget = forms.widgets.HiddenInput()
                self.fields[key] = forms.CharField(initial=val, widget=widget)
        else:
            super(PaymentForm, self).__init__(data=data)
        self.action = action
        self.autosubmit = autosubmit
        self.method = method
        self.provider = provider
        self.payment = payment


class CreditCardPaymentForm(PaymentForm):

    number = CreditCardNumberField(label=_('Card Number'), max_length=32,
                                   required=True)
    expiration = CreditCardExpiryField()
    cvv2 = CreditCardVerificationField(
        label=_('CVV2 Security Number'), required=False, help_text=_(
            'Last three digits located on the back of your card.'
            ' For American Express the four digits found on the front side.'))

    def __init__(self, *args, **kwargs):
        super(CreditCardPaymentForm, self).__init__(
            hidden_inputs=False, *args,  **kwargs)
        if hasattr(self, 'VALID_TYPES'):
            self.fields['number'].valid_types = self.VALID_TYPES


class CreditCardPaymentFormWithName(CreditCardPaymentForm):

    name = CreditCardNameField(label=_('Name on Credit Card'), max_length=128)

    def __init__(self, *args, **kwargs):
        super(CreditCardPaymentFormWithName, self).__init__(*args, **kwargs)
        name_field = self.fields.pop('name')
        fields = OrderedDict({'name': name_field})
        fields.update(fields)
        self.fields = fields
