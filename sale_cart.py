# This file is part of sale_cart_discount module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval
from trytond.config import config as config_

__all__ = ['SaleCart']

STATES = {
    'readonly': (Eval('state') != 'draft')
    }
DIGITS = config_.getint('product', 'price_decimal', default=4)
DISCOUNT_DIGITS = config_.getint('product', 'discount_decimal', default=4)


class SaleCart:
    __metaclass__ = PoolMeta
    __name__ = 'sale.cart'
    gross_unit_price = fields.Numeric('Gross Price', digits=(16, DIGITS),
        states=STATES)
    discount = fields.Numeric('Discount', digits=(16, DISCOUNT_DIGITS),
        states=STATES)

    @classmethod
    def __setup__(cls):
        super(SaleCart, cls).__setup__()
        cls.unit_price.states['readonly'] = True
        cls.unit_price.digits = (20, DIGITS + DISCOUNT_DIGITS)
        if 'discount' not in cls.product.on_change:
            cls.product.on_change.add('discount')
        if 'discount' not in cls.untaxed_amount.on_change_with:
            cls.untaxed_amount.on_change_with.add('discount')
        if 'gross_unit_price' not in cls.untaxed_amount.on_change_with:
            cls.untaxed_amount.on_change_with.add('gross_unit_price')
        if 'discount' not in cls.quantity.on_change:
            cls.quantity.on_change.add('discount')

    @staticmethod
    def default_discount():
        return Decimal(0)

    def update_prices(self):
        unit_price = None
        gross_unit_price = self.gross_unit_price

        if self.gross_unit_price is not None and self.discount is not None:
            unit_price = self.gross_unit_price * (1 - self.discount)
            digits = self.__class__.unit_price.digits[1]
            unit_price = unit_price.quantize(Decimal(str(10.0 ** -digits)))

            if self.discount != 1:
                gross_unit_price = unit_price / (1 - self.discount)
            digits = self.__class__.gross_unit_price.digits[1]
            gross_unit_price = gross_unit_price.quantize(
                Decimal(str(10.0 ** -digits)))

        self.gross_unit_price = gross_unit_price
        self.unit_price = unit_price

    @fields.depends('gross_unit_price', 'discount', 'product')
    def on_change_gross_unit_price(self):
        return self.update_prices()

    @fields.depends('gross_unit_price', 'discount', 'product')
    def on_change_discount(self):
        return self.update_prices()

    def on_change_product(self):
        super(SaleCart, self).on_change_product()

        if not self.product:
            return

        if self.unit_price:
            self.gross_unit_price = self.unit_price
            self.discount = Decimal(0)
            self.update_prices()
        if not self.discount:
            self.discount = Decimal(0)

    def on_change_quantity(self):
        super(SaleCart, self).on_change_quantity()
        if self.unit_price:
            self.gross_unit_price = self.unit_price
            self.update_prices()

    def get_sale_line(self, sale):
        line = super(SaleCart, self).get_sale_line(sale)
        line.discount = self.discount # force discount value
        return line

