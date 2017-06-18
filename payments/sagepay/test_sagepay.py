from __future__ import unicode_literals
from unittest import TestCase
from mock import patch, MagicMock, Mock

from . import SagepayProvider
from .. import PaymentStatus
from ..meta import create_get_address

VENDOR = 'abcd1234'
ENCRYPTION_KEY = '1234abdd1234abcd'


class Payment(Mock):
    id = 1
    variant = 'sagepay'
    currency = 'USD'
    total = 100
    status = PaymentStatus.WAITING
    transaction_id = None
    captured_amount = 0
    billing_first_name = 'John'
    billing_last_name = 'Smith'
    billing_address_1 = 'JohnStreet 23'
    billing_address_2 = ''
    billing_city = 'Neches'
    billing_postcode = "75779"
    billing_country_code = "US"
    billing_country_area = "Tennessee"

    get_billing_address = create_get_address("billing")
    get_shipping_address = create_get_address("billing")



    def get_process_url(self):
        return 'http://example.com'

    def get_failure_url(self):
        return 'http://cancel.com'

    def get_success_url(self):
        return 'http://success.com'

    def change_status(self, status):
        self.status = status


class TestSagepayProvider(TestCase):

    def setUp(self):
        self.payment = Payment()
        self.provider = SagepayProvider(
            vendor=VENDOR, encryption_key=ENCRYPTION_KEY)

    @patch('payments.sagepay.redirect')
    def test_provider_raises_redirect_needed_on_success(self, mocked_redirect):
        data = {'Status': 'OK'}
        data = "&".join(u"%s=%s" % kv for kv in data.items())
        with patch.object(SagepayProvider, 'aes_dec', return_value=data):
            self.provider.process_data(self.payment, MagicMock())
            self.assertEqual(self.payment.status, PaymentStatus.CONFIRMED)
            self.assertEqual(self.payment.captured_amount, self.payment.total)

    @patch('payments.sagepay.redirect')
    def test_provider_raises_redirect_needed_on_failure(self, mocked_redirect):
        data = {'Status': ''}
        data = "&".join(u"%s=%s" % kv for kv in data.items())
        with patch.object(SagepayProvider, 'aes_dec', return_value=data):
            self.provider.process_data(self.payment, MagicMock())
            self.assertEqual(self.payment.status, PaymentStatus.REJECTED)
            self.assertEqual(self.payment.captured_amount, 0)

    def test_provider_encrypts_data(self):
        data = self.provider.get_hidden_fields(self.payment)
        decrypted_data = self.provider.aes_dec(data['Crypt'])
        self.assertIn(self.payment.billing_first_name, str(decrypted_data))

    def test_encrypt_method_returns_valid_data(self):
        encrypted = self.provider.aes_enc('mirumee')
        self.assertEqual(encrypted, b'@e63c293672f50b9c8e291831facb4e4f')
