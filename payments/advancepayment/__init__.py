""" advance payment provider """


from __future__ import unicode_literals

import logging

from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .forms import IBANBankingForm
from .. import PaymentError, PaymentStatus, RedirectNeeded
from ..core import BasicProvider

class AdvancePaymentProvider(BasicProvider):
    '''
        banking software or user confirms transaction (with token).
        The user gets only the id, the seller can confirm with the token
        The form is only needed to show the user the data
    '''

    def __init__(self, iban, bic, **kwargs):
        if len(iban) <= 10 or len(bic) != 11:
            raise ImproperlyConfigured("Wrong iban or bic")
        self.iban=iban
        self.bic=bic
        super(AdvancePaymentProvider, self).__init__(**kwargs)

    def initialize_form(self):
        return {
            'iban': self.iban,
            'bic': self.bic
        }

    def get_form(self, payment, data=None):
        if not payment.id:
            payment.save()
        if not data:
            return IBANBankingForm(self.initialize_form().update({"orderid": payment.id}))
        if self._capture:
            payment.change_status(PaymentStatus.WAITING)
        else:
            payment.change_status(PaymentStatus.PREAUTH)
        raise RedirectNeeded(payment.get_success_url())

    def process_data(self, payment, request):
        payment.change_status(PaymentStatus.CONFIRMED)
        return HttpResponseRedirect()

    def capture(self, payment, amount=None):
        if not amount:
            amount = payment.total
        return amount

    def release(self, payment):
        if payment.status == PaymentStatus.PREAUTH:
            payment.change_status(PaymentStatus.WAITING)

    def refund(self, payment, amount=None):
        if not amount:
            amount = payment.total
        payment.change_status(PaymentStatus.REFUNDED)
        return amount
