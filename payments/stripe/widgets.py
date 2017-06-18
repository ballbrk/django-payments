from __future__ import unicode_literals

try:
    from django.forms.utils import flatatt
except ImportError:
    from django.forms.util import flatatt
from django.forms.widgets import Input, HiddenInput
from django.utils.html import format_html
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django import VERSION as DJANGO_VERSION


class StripeCheckoutWidget(Input):
    is_hidden = True

    def __init__(self, provider, payment, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        kwargs['attrs'] = {
            'class': 'stripe-button',
            'data-key': provider.public_key,
            'data-image': provider.image,
            'data-name': provider.name,
            'data-description': payment.description or _('Total payment'),
            # Stripe accepts cents
            'data-amount': int(payment.total * 100),
            'data-currency': payment.currency
        }
        kwargs['attrs'].update(attrs)
        super(StripeCheckoutWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        if DJANGO_VERSION >= (1, 11, 0):
            final_attrs = self.build_attrs(self.attrs, attrs)
        else:
            final_attrs = self.build_attrs(attrs)
        final_attrs["src"] = "https://checkout.stripe.com/checkout.js"
        del final_attrs['id']
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_text(self._format_value(value))
        return format_html('<script{0}></script>', flatatt(final_attrs))


class StripeWidget(HiddenInput):

    class Media:
        js = ['https://js.stripe.com/v2/',
              'js/payments/stripe.js']
    if DJANGO_VERSION >= (1, 11, 0):
        def build_attrs(self, base_attrs, extra_attrs=None):
            extra_attrs = dict(extra_attrs or {}, id='id_stripe_token')
            return super(StripeWidget, self).build_attrs(base_attrs, extra_attrs)
    else:
        def build_attrs(self, extra_attrs=None, **kwargs):
            extra_attrs = dict(extra_attrs or {}, id='id_stripe_token')
            return super(StripeWidget, self).build_attrs(extra_attrs, **kwargs)
