""" cash on delivery payment provider """


from __future__ import unicode_literals

import logging

from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .forms import OrderIdForm
from .. import PaymentError, PaymentStatus, RedirectNeeded
from ..core import BasicProvider

class DirectPaymentProvider(BasicProvider):
    '''
        Payment is done manually e.g. cash on delivery
        Because of that there is no limitation and payments are confirmed without checks

        withorderform:
            show Form with order number
    '''

    def __init__(self, withorderform=False, **kwargs):
        super(DirectPaymentProvider, self).__init__(**kwargs)
        self.withorderform = withorderform
        if not self._capture:
            raise ImproperlyConfigured(
                'Direct Payments do not support pre-authorization.')

    def get_form(self, payment, data=None):
        if not payment.id:
            payment.save()
        if self.withorderform:
            if not data or not data.get("orderid", None):
                return OrderIdForm({"orderid": payment.id}, payment, self)
        payment.change_status(PaymentStatus.CONFIRMED)
        raise RedirectNeeded(payment.get_success_url())

    def refund(self, payment, amount=None):
        if not amount:
            amount = payment.total
        payment.change_status(PaymentStatus.REFUNDED)
        return amount
