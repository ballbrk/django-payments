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

        withreference:
            show Form with order number
        safer:
            if you don't verify the name; don't allow people supplying other order numbers (by adding token)
            is much longer so default off
        prefix:
            reference: add prefix to payment id

    '''

    def __init__(self, withreference=False, safer=False, prefix="", **kwargs):
        super(DirectPaymentProvider, self).__init__(**kwargs)
        self.withreference = withreference
        self.prefix = prefix
        self.safer = safer
        if not self._capture:
            raise ImproperlyConfigured(
                'Direct Payments do not support pre-authorization.')

    def get_form(self, payment, data=None):
        if not payment.id:
            payment.save()
        if not payment.transaction_id:
            if self.safer:
                payment.transaction_id = "{}{}-".format(self.prefix, payment.id, payment.token)
            else:
                payment.transaction_id = "{}{}".format(self.prefix, payment.id)
            payment.save()
        if self.withreference:
            if not data or not data.get("order", None):
                return OrderIdForm({"order": payment.transaction_id}, payment, self)
        payment.change_status(PaymentStatus.CONFIRMED)
        raise RedirectNeeded(payment.get_success_url())

    def refund(self, payment, amount=None):
        if not amount:
            amount = payment.total
        payment.change_status(PaymentStatus.REFUNDED)
        return amount
