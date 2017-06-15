from __future__ import unicode_literals
try:
    # For Python 3.0 and later
    from urllib.error import URLError
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import URLError
    from urllib import urlencode
from django.http import HttpResponseRedirect

from .. import PaymentError, PaymentStatus, RedirectNeeded
from ..core import BasicProvider
import requests
import uuid
import datetime
import base64
import os
import email.utils
import hmac


# Capture: if False ORDER is used
class PaydirektProvider(BasicProvider):
    '''
    paydirekt payment provider

    api_key:
        seller key, assigned by paydirekt
    secret:
        seller secret key
    endpoint:
        which endpoint to use
    '''
    token_raw = None
    token_uuid = None
    access_token = None
    expires_in = None
    api_version = None

    translate_status = {
        "APPROVED": PaymentStatus.CONFIRMED,
        "OPEN": PaymentStatus.PREAUTH,
        "PENDING": PaymentStatus.WAITING,
        "REJECTED": PaymentStatus.REJECTED,
        "CANCELED": PaymentStatus.ERROR,
        "CLOSED": PaymentStatus.CONFIRMED,
        "EXPIRED": PaymentStatus.ERROR,
    }
    header_default = {
        "Content-Type": "application/hal+json;charset=utf-8",
    }


    def __init__(self, api_key, secret, endpoint="https://api.sandbox.paydirekt.de", overcapture=False, api_version="v1", **kwargs):
        self.api_key = api_key
        self.secret = secret
        self.endpoint = endpoint
        self.api_version = api_version
        self.overcapture = overcapture
        super(PaydirektProvider, self).__init__(**kwargs)

    def retrieve_oauth_token(self):
        self.token_uuid = uuid.uuid4()
        nonce = base64.urlsafe_b64encode(os.urandom(64))
        date = datetime.datetime.utcnow()
        strsign = self.token_uuid+date.strftime("%Y%m%d%H%M%S")+self.api_key+nonce
        h = hmac.new(strsign, msg=base64.urlsafe_b64encode(self.secret.encode("utf-8")), digestmod='sha256')

        header = PaydirektProvider.header_default.copy()
        header.update(("X-Auth-Key", self.api_key))
        header.update(("X-Request-ID", self.token_uuid))

        header.update(("X-Auth-Code", base64.urlsafe_b64encode(h.digest())))
        header.update(("Date", email.utils.format_datetime(date, usegmt=True))
        body = {
            "grantType" : "api_key",
            "randomNonce" : nonce
        }
        response = request.post(f"/api/merchantintegration/{self.api_version}/token/obtain", data=body, header=header)
        response.raise_for_status()
        self.token_raw = response.json()
        self.access_token = self.token_raw["access_token"]
        self.expires_in = datetime.fromtimestamp(self.token_raw["expires_in"], datetime.timezone.utc)

    def check_and_update_token(self):
        if not self.expires_in or self.expires_in >= datetime.datetime.now(datetime.timezone.utc):
            self.retrieve_oauth_token()

    def get_form(self, payment, data=None):
        if not payment.id:
            payment.save()
        self.check_and_update_token()
        header = PaydirektProvider.header_default.copy()
        header.update(("Authorization", f"Bearer {self.access_token}"))

        body = {
            "type": getattr(payment, "saletype", "DIRECT_SALE"),
            "totalAmount": payment.total,
            "shippingAmount": payment.delivery,
            #"orderAmount": getattr(payment, "order", None),
            "currency": payment.currency,
            #"items": getattr(payment, "items", None),
            #"shoppingCartType": getattr(payment, "carttype", None),
            "deliveryType": "ORDER" if not self._capture else "DIRECT_SALE",
            "merchantOrderReferenceNumber": str(payment.id),
            "redirectUrlAfterSuccess": payment.get_success_url(),
            "redirectUrlAfterCancellation": payment.get_failure_url(),
            "redirectUrlAfterRejection": payment.get_failure_url(),
            "callbackUrlStatusUpdates": self.get_return_url(payment),
            #"sha256hashedEmailAddress": base64.urlsafe_b64encode(hashlib.sha256(payment.billing_email.encode("utf-8")).digest()),
            "minimumAge": getattr(payment, "minimumage", None),
            "redirectUrlAfterAgeVerificationFailure": payment.get_failure_url(),
            #"note": payment.message[0:37]

        }
        if self.overcapture and body["type"] == "ORDER":
            body.update(("overcapture", True))
        shipping = {
            "addresseeGivenName": payment.billing_first_name,
            "addresseeLastName": payment.billing_last_name,
            "company": getattr(payment, "billing_company", None),
            #"additionalAddressInformation":,
            "street": payment.billing_address_1,
            "streetNr": payment.billing_address_2,
            "zip": payment.billing_postcode,
            "city": payment.billing_city,
            "countryCode": payment.billing_country_code,
            "state": payment.billing_country_area,
            "emailAddress": payment.billing_email
        }
        shipping = {k: v for k, v in shipping.items() if v}
        body = {k: v for k, v in body.items() if v}

        body["shippingAddress"] = shipping

        response = request.post(f"/api/merchantintegration/{self.api_version}/token/obtain", data=body, header=header)
        response.raise_for_status()
        ob = response.json()
        raise RedirectNeeded(ob["approve"])

    def process_data(self, payment, request):
        if request.status != 200:
            return
        try:
            results = json.loads(request.body)
        except (ValueError, TypeError):
            return HttpResponseForbidden('FAILED')
        if response.reasonCode != "APPROVED" and not payment.transaction_id:
            payment.remove()
        else:
            if response.reasonCode == "APPROVED":
                payment.transaction_id = results["checkoutId"]
                if self._capture:
                    payment.change_status(translate_status(results["checkoutStatus"]))
                else:
                    payment.change_status(PaymentStatus.PREAUTH)
            else:
                payment.change_status(translate_status(results["checkoutStatus"], self._capture))
            payment.save()

    def capture(self, payment, amount=None):
        if not amount:
            amount = payment.total
        self.check_and_update_token()
        header = PaydirektProvider.header_default.copy()
        header.update(("Authorization", f"Bearer {self.access_token}"))
        body = {
            "amount": amount,
            "callbackUrlStatusUpdates", self.get_return_url(payment)
        }
        response = request.post(f"/api/checkout/{self.api_version}/checkouts/{payment.transaction_id}/captures", data=body, header=header)
        response.raise_for_status()
        ob = response.json()
        return ob["amount"]

    def release(self, payment):
        self.check_and_update_token()
        header = PaydirektProvider.header_default.copy()
        header.update(("Authorization", f"Bearer {self.access_token}"))
        response = request.post(f"/api/checkout/{self.api_version}/checkouts/{payment.transaction_id}/captures/close", header=header)
        response.raise_for_status()

    def refund(self, payment, amount=None):
        if not amount:
            amount = payment.total
        self.check_and_update_token()
        header = PaydirektProvider.header_default.copy()
        header.update(("Authorization", f"Bearer {self.access_token}"))
        body = {
            "amount": amount,
            "callbackUrlStatusUpdates", self.get_return_url(payment)
        }
        response = request.post(f"/api/checkout/{self.api_version}/checkouts/{payment.transaction_id}/refunds", data=body, header=header)
        response.raise_for_status()
        ob = response.json()
        return ob["amount"]
