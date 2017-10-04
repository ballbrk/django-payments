
from decimal import Decimal
from .models import AbstractBasePayment
from . import PaymentStatus, PurchasedItem
from .utils import create_get_address
from datetime import datetime

def create_test_payment(_variant="undefined", _token="342"):
    class TestPayment(AbstractBasePayment):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
        id = 523
        pk = id
        description = 'payment'
        currency = 'USD'
        delivery = Decimal(10.8)
        status = PaymentStatus.WAITING
        message = ""
        tax = Decimal(10)
        token = _token
        total = Decimal(100)
        captured_amount = Decimal(0)
        extra_data = ""
        variant = _variant
        transaction_id = ""
        created = datetime.now()
        modified = datetime.now()

        billing_first_name = 'John'
        billing_last_name = 'Smith'
        billing_address_1 = 'JohnStreet 23'
        billing_address_2 = ''
        billing_city = 'Neches'
        billing_postcode = "75779"
        billing_country_code = "US"
        billing_country_area = "Tennessee"
        billing_email = "example@example.com"

        customer_ip_address = "192.78.6.6"

        get_billing_address = create_get_address("billing")
        get_shipping_address = create_get_address("billing")

        def change_status(self, status, message=""):
            self.status = status
            self.message = message

        def change_fraud_status(self, status, message='', commit=True):
            self.fraud_status = status
            self.fraud_message = message

        def get_purchased_items(self):
            return [
                PurchasedItem(
                    name='foo', quantity=Decimal('10'), price=Decimal('20'),
                    currency='USD', sku='bar')]

        def get_failure_url(self):
            return 'http://cancel.com'

        def get_process_url(self):
            return 'http://example.com'

        def get_success_url(self):
            return 'http://success.com'

        def save(self):
            return self
    return TestPayment
