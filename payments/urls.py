from django.urls import path

from payments import views

urlpatterns = [
    path('', views.home, name='home'),
    path('item/<int:item_id>', views.item_page, name='item-page'),
    path('buy/<int:item_id>', views.buy_item, name='buy-item'),
    path('order/<int:order_id>', views.order_page, name='order-page'),
    path('buy-order/<int:order_id>', views.buy_order, name='buy-order'),
    path('item-intent/<int:item_id>', views.item_intent_page, name='item-intent-page'),
    path('buy-intent/<int:item_id>', views.buy_item_intent, name='buy-item-intent'),
    path('buy-order-intent/<int:order_id>', views.buy_order_intent, name='buy-order-intent'),
]
