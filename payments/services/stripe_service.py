from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import stripe
from django.conf import settings

# RequestsClient avoids httpx proxy issues (e.g. socks4:// on Windows).
stripe.default_http_client = stripe.RequestsClient(timeout=30)


class StripeConfigError(Exception):
    pass


if TYPE_CHECKING:
    from payments.models import Discount, Item, Order, Tax


class StripeService:
    """Stripe API wrapper with multi-currency key selection."""

    PLACEHOLDER_MARKERS = ('your_', '_key', 'change-me', 'example')

    @classmethod
    def _validate_key(cls, key: str, key_name: str) -> None:
        if not key or not key.strip():
            raise StripeConfigError(f'{key_name} is not configured.')
        normalized = key.strip().lower()
        if any(marker in normalized for marker in cls.PLACEHOLDER_MARKERS):
            raise StripeConfigError(
                f'{key_name} looks like a placeholder. '
                'Set real test keys from https://dashboard.stripe.com/test/apikeys'
            )
        if key_name.startswith('Stripe secret') and not key.startswith('sk_'):
            raise StripeConfigError(f'{key_name} must start with sk_.')
        if key_name.startswith('Stripe publishable') and not key.startswith('pk_'):
            raise StripeConfigError(f'{key_name} must start with pk_.')

    @classmethod
    def _configure(cls, currency: str) -> None:
        api_key = settings.STRIPE_SECRET_KEYS.get(currency.lower(), '')
        cls._validate_key(api_key, f'Stripe secret key for {currency.upper()}')
        stripe.api_key = api_key.strip()

    @staticmethod
    def get_publishable_key(currency: str) -> str:
        publishable_key = settings.STRIPE_PUBLISHABLE_KEYS.get(currency.lower(), '')
        StripeService._validate_key(
            publishable_key,
            f'Stripe publishable key for {currency.upper()}',
        )
        return publishable_key.strip()

    @classmethod
    def _build_line_item(cls, item: Item, tax: Tax | None = None) -> dict:
        line_item = {
            'price_data': {
                'currency': item.currency,
                'product_data': {
                    'name': item.name,
                    'description': item.description or None,
                },
                'unit_amount': item.price_in_cents,
            },
            'quantity': 1,
        }
        if tax and tax.stripe_tax_rate_id:
            line_item['tax_rates'] = [tax.stripe_tax_rate_id]
        return line_item

    @classmethod
    def create_checkout_session_for_item(cls, item: Item) -> stripe.checkout.Session:
        cls._configure(item.currency)
        return stripe.checkout.Session.create(
            mode='payment',
            line_items=[cls._build_line_item(item)],
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
        )

    @classmethod
    def create_checkout_session_for_order(cls, order: Order) -> stripe.checkout.Session:
        currency = order.currency
        cls._configure(currency)

        line_items = [
            cls._build_line_item(item, order.tax)
            for item in order.items.all()
        ]

        session_params: dict = {
            'mode': 'payment',
            'line_items': line_items,
            'success_url': settings.STRIPE_SUCCESS_URL,
            'cancel_url': settings.STRIPE_CANCEL_URL,
        }

        if order.discount and order.discount.stripe_coupon_id:
            session_params['discounts'] = [
                {'coupon': order.discount.stripe_coupon_id},
            ]

        return stripe.checkout.Session.create(**session_params)

    @classmethod
    def create_payment_intent_for_item(cls, item: Item) -> stripe.PaymentIntent:
        cls._configure(item.currency)
        return stripe.PaymentIntent.create(
            amount=item.price_in_cents,
            currency=item.currency,
            automatic_payment_methods={'enabled': True},
            metadata={'item_id': str(item.pk)},
        )

    @classmethod
    def create_payment_intent_for_order(cls, order: Order) -> stripe.PaymentIntent:
        currency = order.currency
        cls._configure(currency)

        subtotal = sum(item.price_in_cents for item in order.items.all())
        amount = subtotal

        if order.discount:
            discount_amount = int(
                Decimal(subtotal) * order.discount.percent_off / Decimal('100')
            )
            amount = max(subtotal - discount_amount, 0)

        if order.tax:
            tax_amount = int(Decimal(amount) * order.tax.percentage / Decimal('100'))
            amount += tax_amount

        return stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            automatic_payment_methods={'enabled': True},
            metadata={'order_id': str(order.pk)},
        )

    @classmethod
    def ensure_discount_coupon(cls, discount: Discount, currency: str) -> str:
        if discount.stripe_coupon_id:
            return discount.stripe_coupon_id

        cls._configure(currency)
        coupon = stripe.Coupon.create(
            name=discount.name,
            percent_off=float(discount.percent_off),
            duration='forever',
        )
        discount.stripe_coupon_id = coupon.id
        discount.save(update_fields=['stripe_coupon_id'])
        return coupon.id

    @classmethod
    def ensure_tax_rate(cls, tax: Tax, currency: str) -> str:
        if tax.stripe_tax_rate_id:
            return tax.stripe_tax_rate_id

        cls._configure(currency)
        tax_rate = stripe.TaxRate.create(
            display_name=tax.name,
            percentage=float(tax.percentage),
            inclusive=False,
        )
        tax.stripe_tax_rate_id = tax_rate.id
        tax.save(update_fields=['stripe_tax_rate_id'])
        return tax_rate.id
