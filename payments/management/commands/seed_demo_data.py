from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from payments.models import Currency, Discount, Item, Order, Tax

DEMO_ITEMS = [
    {
        'pk': 1,
        'name': 'Premium Plan',
        'description': 'Monthly subscription plan',
        'price': Decimal('29.99'),
        'currency': Currency.USD,
    },
    {
        'pk': 2,
        'name': 'Consulting Hour',
        'description': 'One hour of expert consulting',
        'price': Decimal('150.00'),
        'currency': Currency.USD,
    },
    {
        'pk': 3,
        'name': 'Design Package',
        'description': 'UI/UX design package',
        'price': Decimal('99.00'),
        'currency': Currency.EUR,
    },
]


class Command(BaseCommand):
    help = 'Create demo data and reset admin credentials.'

    def handle(self, *args, **options):
        items = []
        for data in DEMO_ITEMS:
            item_pk = data.pop('pk')
            item, _ = Item.objects.update_or_create(pk=item_pk, defaults=data)
            data['pk'] = item_pk
            items.append(item)

        discount, _ = Discount.objects.update_or_create(
            pk=1,
            defaults={
                'name': 'Launch promo',
                'percent_off': Decimal('10.00'),
            },
        )
        tax, _ = Tax.objects.update_or_create(
            pk=1,
            defaults={
                'name': 'VAT',
                'percentage': Decimal('20.00'),
            },
        )

        order, _ = Order.objects.update_or_create(
            pk=1,
            defaults={'discount': discount, 'tax': tax},
        )
        order.items.set(items[:2])

        User = get_user_model()
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com'},
        )
        admin.set_password('admin123')
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        self.stdout.write(self.style.SUCCESS('Demo data ready. Admin: admin / admin123'))
