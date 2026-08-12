from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Currency(models.TextChoices):
    USD = 'usd', 'USD'
    EUR = 'eur', 'EUR'


class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD,
    )

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return self.name

    @property
    def price_in_cents(self) -> int:
        return int(self.price * 100)


class Discount(models.Model):
    name = models.CharField(max_length=255)
    percent_off = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    stripe_coupon_id = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} ({self.percent_off}%)'


class Tax(models.Model):
    name = models.CharField(max_length=255)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    stripe_tax_rate_id = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} ({self.percentage}%)'


class Order(models.Model):
    items = models.ManyToManyField(Item, related_name='orders')
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
    )
    tax = models.ForeignKey(
        Tax,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Order #{self.pk}'

    @property
    def currency(self) -> str:
        currencies = {item.currency for item in self.items.all()}
        if len(currencies) != 1:
            raise ValueError('All items in an order must share the same currency.')
        return currencies.pop()

    @property
    def total_price(self):
        return sum(item.price for item in self.items.all())
