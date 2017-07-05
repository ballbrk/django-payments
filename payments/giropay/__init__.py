""" paydirekt payment provider """


from __future__ import unicode_literals
try:
    # For Python 3.0 and later
    from urllib.error import URLError
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import URLError
    from urllib import urlencode

import uuid
from datetime import datetime, timezone, timedelta
from base64 import urlsafe_b64encode, urlsafe_b64decode
import os
import email.utils
import hmac
import simplejson as json
import time
import logging

import requests
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.conf import settings

from .. import PaymentError, PaymentStatus, RedirectNeeded
from ..core import BasicProvider


def check_response(response, response_json):
    if response.status_code not in [200, 201] or response_json["rc"] != 4000:
        if response_json:
            try:
                error_code = response_json["rc"]
                gateway_error = response_json["msg"]
                raise PaymentError(str(response.status_code), code=error_code, gateway_message=gateway_error)
            except KeyError:
                raise PaymentError(str(response.status_code))
        else:
            raise PaymentError(str(response.status_code))


# Capture: if False ORDER is used
class PaydirektProvider(BasicProvider):
    '''
    Giropay Paydirekt payment provider

    api_key:
        seller key, assigned by paydirekt
    secret:
        seller secret key (=encoded in base64)
    endpoint:
        which endpoint to use
    '''
    checkout_field_order = ["merchantId", "projectId", "merchantTxId", "amount", "currency", "purpose", "type", "shoppingCartType", "CustomerId", "shippingAmount", "shippingAddresseFirstName",\
    "shippingAddresseLastName", "shippingCompany", "shippingAdditionalAddressInformation", "shippingStreet", "shippingStreetNumber", "shippingZipCode", "shippingCity", "shippingCountry", "shippingEmail",  "merchantReconciliationReferenceNumber", "orderAmount", "orderId", "cart", "invoiceId", "customerMail", "minimumAge", "urlRedirect", "urlNotify"]

    #  capture/refund
    cr_field_order = ["merchantId", "projectId", "merchantTxId", "amount", "currency", "purpose", "reference", "merchantReconciliationReferenceNumber", "final"]
    path_checkout = "{}/girocheckout/api/v2/transaction/start"
    path_capture = "{}/girocheckout/api/v2/transaction/capture"
    path_refund = "{}/girocheckout/api/v2/transaction/refund"

    endpoint = "https://payment.girosolution.de"

    # DANGER: there is no playground url, check if Project has test status
    def __init__(self, merchantId, projectId, secret, overcapture=False, **kwargs):
        self.merchantId = merchantId
        self.projectId = projectId
        self.secret = secret
        self.endpoint = endpoint
        self.overcapture = overcapture
        super(PaydirektProvider, self).__init__(**kwargs)
        if not self._capture:
            raise ImproperlyConfigured(
                'Giropay paydirekt does not support pre-authorization.')

    def auth_for_dict(self, dictob, order):
        hmacob = hmac.new(self.secret, digestmod="md5")
        dictob["merchantId"] = self.merchantId
        dictob["projectId"] = self.projectId
        for field in order:
            if dictob.get(field, None):
                hmacob.update(str(dictob.get(field)).encode("utf8"))
        dictob["hash"] = hmacob.hexdigest()
        return dictob

    def get_form(self, payment, data=None):
        if not payment.id:
            payment.save()
        # email_hash = sha256(payment.billing_email.encode("utf-8")).digest())
        shipping = payment.get_shipping_address()
        # TODO: seems streetnr is in address_1
        body = {
            "type": "ORDER" if not self._capture else "DIRECT_SALE",
            "amount": int(payment.total*100),
            "shippingAmount": int(payment.delivery*100),
            "currency": payment.currency,
            "shippingAddresseeGivenName": shipping["first_name"],
            "shippingAddresseeLastName": shipping["last_name"],
            "shippingCompany": shipping.get("company", None),
            #"additionalAddressInformation": shipping["address_2"],
            "shippingStreet": shipping["address_1"],
            "shippingStreetNumber": shipping["address_2"],
            "shippingZipCode": shipping["postcode"],
            "shippingCity": shipping["city"],
            "shippingCountry": shipping["country_code"],
            "shippingEmail": payment.billing_email
            #"items": getattr(payment, "items", None),
            #"shoppingCartType": getattr(payment, "carttype", None),
            #"deliveryType": getattr(payment, "deliverytype", None),
            # payment id can repeat if different shop systems are used
            "merchantTxId": "{}-{}".format(self.projectId, payment.id),
            "urlRedirect": payment.get_success_url(),
            "urlNotify": self.get_return_url(payment),
            "minimumAge": getattr(payment, "minimumage", None),
        }
        if self.overcapture and body["type"] == "ORDER":
            body["overcapture"] = True

        body = {k: v for k, v in body.items() if v}
        self.auth_for_dict(body, self.checkout_field_order)

        response = requests.post(self.path_checkout.format(self.endpoint), data=body)
        json_response = json.loads(response.text)
        check_response(response, json_response)
        raise RedirectNeeded(json_response["redirect"])

    def process_data(self, payment, request):
        try:
            results = json.loads(request.body, use_decimal=True)
        except (ValueError, TypeError):
            logging.error("Payment failed because of unparseable object")
            return HttpResponseForbidden('FAILED')
        if not payment.transaction_id:
            payment.transaction_id = results["gcBackendTxId"]
        if results["gcResultPayment"] == "APPROVED":
            if self._capture:
                payment.change_status(PaymentStatus.CONFIRMED)
            else:
                payment.change_status(PaymentStatus.PREAUTH)
        else:
            payment.change_status(PaymentStatus.ERROR)
        return HttpResponse('OK')

    def capture(self, payment, amount=None, final=False):
        if not amount:
            amount = payment.total
        body = {
            "amount": int(amount*100),
            "currency": self.currency,
            "finalCapture": final,
            "purpose": "capture",
            "merchantTxId": "{}-{}".format(self.projectId, payment.id),
            "reference": payment.transaction_id,
            "final": final
        }
        self.auth_for_dict(body, self.rc_field_order)
        response = requests.post(self.path_capture.format(self.endpoint), \
                                 data=body)
        json_response = json.loads(response.text, use_decimal=True)
        check_response(response, json_response)
        return decimal.Decimal("{}.{}".format(divmod(json_response["amount"], 100)))

    def refund(self, payment, amount=None):
        if not amount:
            amount = payment.total
        body = {
            "amount": int(amount*100),
            "currency": self.currency,
            "finalCapture": final,
            "purpose": "capture",
            "merchantTxId": "{}-{}".format(self.projectId, payment.id),
            "reference": payment.transaction_id,
            "final": final
        }
        self.auth_for_dict(body, self.rc_field_order)
        response = requests.post(self.path_capture.format(self.endpoint), \
                                 data=body)
        json_response = json.loads(response.text, use_decimal=True)
        check_response(response, json_response)
        return decimal.Decimal("{}.{}".format(divmod(json_response["amount"], 100)))