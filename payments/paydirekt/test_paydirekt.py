from unittest import TestCase
try:
    from urllib.error import URLError
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
    from urllib2 import URLError
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from . import PaydirektProvider
from .. import FraudStatus, PaymentError, PaymentStatus, RedirectNeeded

VARIANT = 'paydirekt'
API_KEY = '5a4dae68-2715-4b1e-8bb2-2c2dbe9255f6'
SECRET = '123abc'

PROCESS_DATA = {
  "checkoutId" : "64e0bd1f-c3a3-47e1-aaff-75e690c062f8",
  "merchantOrderReferenceNumber" : "order-A12223412",
  "checkoutStatus" : "APPROVED"
}

class Payment(object):
    id = 1
    variant = VARIANT
    currency = 'EUR'
    total = 100
    status = PaymentStatus.WAITING
    fraud_status = ''

    def get_process_url(self):
        return 'http://example.com'

    def get_failure_url(self):
        return 'http://cancel.com'

    def get_success_url(self):
        return 'http://success.com'

    def change_status(self, new_status):
        self.status = new_status

    def change_fraud_status(self, fraud_status):
        self.fraud_status = fraud_status


class TestPaydirektProvider(TestCase):

    def setUp(self):
        self.payment = Payment()
        self.provider = PaydirektProvider(API_KEY, SECRET)

    def test_process_data_works(self):
        request = MagicMock()
        request.json = lambda : PROCESS_DATA.copy()
        response = self.provider.process_data(self.payment, request)
        self.assertEqual(self.payment.status, verification_status)
        self.assertEqual(response.status_code, 200)
