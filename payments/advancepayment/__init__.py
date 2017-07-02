""" advance payment provider """


from __future__ import unicode_literals

import logging

from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.conf import settings

from .forms import IBANBankingForm
from .. import PaymentError, PaymentStatus, RedirectNeeded
from ..core import BasicProvider

# Capture: if False ORDER is used
class CashOnDeliveryProvider(BasicProvider):
    '''
    nearly stub, because things are done manually
    '''

    def __init__(self, overcapture=False, **kwargs):
        self.overcapture = overcapture
        super(PaydirektProvider, self).__init__(**kwargs)

    def get_form(self, payment, data=None):
        if not payment.id:
            payment.save()
        if not data:
            return IBANBankingForm()
        form = IBANBankingForm(data)
        if not form.is_valid():
            return form
        payment.attrs.IBAN = form.cleaned_data["iban"]
        payment.attrs.BIC = form.cleaned_data["bic"]
        payment.save()
        raise RedirectNeeded(self.get_return_url(payment))

    def process_data(self, payment, request):
        payment.change_status(PaymentStatus.PREAUTH)
        return HttpResponseRedirect(payment.get_success_url())

    def capture(self, payment, amount=None):
        if not amount:
            amount = payment.total
        return amount

    def release(self, payment):
        payment.change_status(PaymentStatus.PREAUTH)

    def refund(self, payment, amount=None):
        if not amount:
            amount = payment.total
        payment.change_status(PaymentStatus.REFUNDED)
        return amount
