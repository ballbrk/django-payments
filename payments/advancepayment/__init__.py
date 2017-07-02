""" advance payment provider """


from __future__ import unicode_literals

import logging

from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.conf import settings

from .forms import IBANBankingForm
from .. import PaymentError, PaymentStatus, RedirectNeeded
from ..core import BasicProvider

class AdvancePaymentProvider(BasicProvider):
    '''
        banking software or user confirms transaction.
        The form is only needed to show the user the data
    '''

    def __init__(self, iban, bic, overcapture=False, **kwargs):
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
            return IBANBankingForm(self.initialize_form().update({"token": self.token}))
        if self._capture:
            payment.change_status(PaymentStatus.WAITING)
        else:
            payment.change_status(PaymentStatus.PREAUTH)
        raise RedirectNeeded(payment.get_success_url())

    # never uncomment! User can confirm himself if he knows the url
    #def process_data(self, payment, request):
    #    payment.change_status(PaymentStatus.CONFIRMED)
    #    return HttpResponseRedirect()

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
