from datetime import date

from django.utils.translation import ugettext_lazy as _


def get_month_choices():
    month_choices = [(str(x), '%02d' % (x,)) for x in range(1, 13)]
    return [('', _('Month'))] + month_choices


def get_year_choices():
    year_choices = [(str(x), str(x)) for x in range(
        date.today().year, date.today().year + 15)]
    return [('', _('Year'))] + year_choices



from django.db import models

def alias_class(name):
    def getalias(self):
        return getattr(self, name)
    def delalias(self):
        delattr(self, name)
    def setalias(self, value):
        setattr(self, name, value)
    return property(setalias, getalias, delalias)


def create_get_address(typename):
    """ create getter  """
    # performance
    # most performant would be exec but in banking area people are more conservative
    first_name = "{}_first_name".format(typename)
    last_name = "{}_last_name".format(typename)
    address_1 = "{}_address_1".format(typename)
    address_2 = "{}_address_2".format(typename)
    city = "{}_city".format(typename)
    postcode = "{}_postcode".format(typename)
    country_code = "{}_country_code".format(typename)
    country_area = "{}_country_area".format(typename)
    def _get_address(self):
        return {
            "first_name": getattr(self, first_name, None),
            "last_name": getattr(self, last_name, None),
            "address_1": getattr(self, address_1, None),
            "address_2": getattr(self, address_2, None),
            "city": getattr(self, city, None),
            "postcode": getattr(self, postcode, None),
            "country_code": getattr(self, country_code, None),
            "country_area": getattr(self, country_area, None)}
    return _get_address

def add_address_to_class(typename):
    """ add address with prefix typename to class, add getter method """
    first_name = "{}_first_name".format(typename)
    last_name = "{}_last_name".format(typename)
    address_1 = "{}_address_1".format(typename)
    address_2 = "{}_address_2".format(typename)
    city = "{}_city".format(typename)
    postcode = "{}_postcode".format(typename)
    country_code = "{}_country_code".format(typename)
    country_area = "{}_country_area".format(typename)
    def class_to_customize(dclass):
        setattr(dclass, first_name, models.CharField(max_length=256, blank=True))
        setattr(dclass, last_name, models.CharField(max_length=256, blank=True))
        setattr(dclass, address_1, models.CharField(max_length=256, blank=True))
        setattr(dclass, address_2, models.CharField(max_length=256, blank=True))
        setattr(dclass, city, models.CharField(max_length=256, blank=True))
        setattr(dclass, postcode, models.CharField(max_length=256, blank=True))
        setattr(dclass, country_code, models.CharField(max_length=2, blank=True))
        setattr(dclass, country_area, models.CharField(max_length=256, blank=True))
        setattr(dclass, "get_{}_address".format(typename), create_get_address(typename))
        return dclass
    return class_to_customize

def transform_address(to, addressname):
    """ create simple transforming method """
    _from = ["first_name", "last_name", "address_1", "address_2", "city", "postcode", "country_code", "country_area"]
    _to = []
    for pos, inp in enumerate(_from):
        if to[pos] != None:
            _to.append((inp, to[pos]))
    def transformer(payment):
        address = getattr(payment, addressname)()
        return {map(lambda key, value: (value, address[key]), _to)}
