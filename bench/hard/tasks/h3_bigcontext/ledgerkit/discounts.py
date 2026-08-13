"""Discount rules.

A rule turns an order subtotal into a discount amount in the same currency.
Rules compose additively: the discount for a tenant is the sum of what each
of its rules yields, capped at the subtotal so an order can never go
negative.
"""
from decimal import Decimal

from .money import Money


class DiscountRule:
    def amount_for(self, subtotal):
        raise NotImplementedError

    def describe(self):
        return type(self).__name__


class PercentageDiscount(DiscountRule):
    """A flat percentage off the subtotal."""

    def __init__(self, percent):
        self.percent = Decimal(str(percent))

    def amount_for(self, subtotal):
        return subtotal * (self.percent / Decimal("100"))

    def describe(self):
        return f"{self.percent}% off"


class FixedDiscount(DiscountRule):
    """A fixed amount off, in a specific currency.

    Only applies when the subtotal is in the same currency, and never more
    than the subtotal itself.
    """

    def __init__(self, money):
        self.money = money

    def amount_for(self, subtotal):
        if subtotal.currency != self.money.currency:
            return Money.zero(subtotal.currency)
        if self.money.amount > subtotal.amount:
            return Money(subtotal.amount, subtotal.currency)
        return self.money

    def describe(self):
        return f"{self.money} off"


class ThresholdDiscount(DiscountRule):
    """A percentage that only kicks in above a threshold."""

    def __init__(self, threshold, percent):
        self.threshold = threshold
        self.percent = Decimal(str(percent))

    def amount_for(self, subtotal):
        if subtotal.currency != self.threshold.currency:
            return Money.zero(subtotal.currency)
        if subtotal.amount < self.threshold.amount:
            return Money.zero(subtotal.currency)
        return subtotal * (self.percent / Decimal("100"))

    def describe(self):
        return f"{self.percent}% off above {self.threshold}"


def total_discount(rules, subtotal):
    """Sum of every rule's discount, capped at the subtotal."""
    acc = Money.zero(subtotal.currency)
    for rule in rules:
        acc = acc + rule.amount_for(subtotal)
    if acc.amount > subtotal.amount:
        return Money(subtotal.amount, subtotal.currency)
    return acc
