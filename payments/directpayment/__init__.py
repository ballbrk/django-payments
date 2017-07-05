""" cash on delivery payment provider """


from __future__ import unicode_literals

import logging

from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .forms import OrderForm
from .. import PaymentError, PaymentStatus, RedirectNeeded
from ..core import BasicProvider

class DirectPaymentProvider(BasicProvider):
    '''
        Payment is done manually e.g. cash on delivery
        Because of that there is no limitation and payments are confirmed without checks
    '''

    def __init__(self, overcapture=False, **kwargs):
        self.overcapture = overcapture
        super(PaydirektProvider, self).__init__(**kwargs)
        if not self._capture:
            raise ImproperlyConfigured(
                'advance payment does not support pre-authorization.')

    def get_form(self, payment, data=None):
        if not payment.id:
            payment.save()
        if not data:
            return OrderForm({"orderid": payment.id, "extracosts": self.extracosts})
        raise RedirectNeeded(self.get_return_url(payment))

    def process_data(self, payment, request):
        payment.change_status(PaymentStatus.CONFIRMED)
        return HttpResponseRedirect(payment.get_success_url())

    def refund(self, payment, amount=None):
        if not amount:
            amount = payment.total
        payment.change_status(PaymentStatus.REFUNDED)
        return amount