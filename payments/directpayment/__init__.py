""" cash on delivery payment provider """


from __future__ import unicode_literals

import logging

from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .. import PaymentError, PaymentStatus, RedirectNeeded
from ..core import BasicProvider

class DirectProvider(BasicProvider):
    '''
        Payment is done manually e.g. cash on delivery
        Because of that there is no limitation and payments are confirmed without checks
    '''

    def __init__(self, **kwargs):
        super(DirectProvider, self).__init__(**kwargs)

    def get_form(self, payment, data=None):
        if not payment.id:
            payment.save()
        raise RedirectNeeded(self.get_return_url(payment))

    def process_data(self, payment, request):
        if self._capture:
            payment.change_status(PaymentStatus.CONFIRMED)
        else:
            payment.change_status(PaymentStatus.PREAUTH)
        return HttpResponseRedirect(payment.get_success_url())

    def capture(self, payment, amount=None):
        if not amount:
            amount = payment.total
        return amount

    def release(self, payment):
        payment.change_status(PaymentStatus.CONFIRMED)

    def refund(self, payment, amount=None):
        if not amount:
            amount = payment.total
        payment.change_status(PaymentStatus.REFUNDED)
        return amount
