from django.contrib import admin

from payments.models import Discount, Item, Order, Tax


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'currency')
    list_filter = ('currency',)
    search_fields = ('name', 'description')


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'percent_off', 'stripe_coupon_id')
    search_fields = ('name',)


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage', 'stripe_tax_rate_id')
    search_fields = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'discount', 'tax')
    list_filter = ('created_at',)
    filter_horizontal = ('items',)
