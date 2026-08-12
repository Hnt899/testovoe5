import stripe
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from payments.models import Item, Order
from payments.services import StripeService
from payments.services.stripe_service import StripeConfigError


def _get_item_or_404(item_id: int) -> Item:
    return get_object_or_404(Item, pk=item_id)


def _get_order_or_404(order_id: int) -> Order:
    order = get_object_or_404(
        Order.objects.prefetch_related('items').select_related('discount', 'tax'),
        pk=order_id,
    )
    if not order.items.exists():
        raise Http404('Order has no items.')
    return order


def _stripe_error_response(exc: Exception) -> JsonResponse:
    if isinstance(exc, StripeConfigError):
        return JsonResponse({'error': str(exc)}, status=500)
    if isinstance(exc, stripe.StripeError):
        return JsonResponse({'error': exc.user_message or str(exc)}, status=502)
    return JsonResponse({'error': 'Payment service unavailable.'}, status=500)


def home(request):
    if request.method == 'HEAD':
        return JsonResponse({'status': 'ok'})
    return redirect('item-page', item_id=1)


@require_GET
def item_page(request, item_id: int):
    item = _get_item_or_404(item_id)
    try:
        stripe_public_key = StripeService.get_publishable_key(item.currency)
    except StripeConfigError as exc:
        return render(
            request,
            'payments/item.html',
            {'item': item, 'stripe_public_key': '', 'config_error': str(exc)},
        )
    return render(
        request,
        'payments/item.html',
        {
            'item': item,
            'stripe_public_key': stripe_public_key,
            'config_error': '',
        },
    )


@require_GET
def buy_item(request, item_id: int):
    item = _get_item_or_404(item_id)
    try:
        session = StripeService.create_checkout_session_for_item(item)
    except (StripeConfigError, stripe.StripeError) as exc:
        return _stripe_error_response(exc)
    return JsonResponse({'id': session.id, 'url': session.url})


@require_GET
def order_page(request, order_id: int):
    order = _get_order_or_404(order_id)
    try:
        stripe_public_key = StripeService.get_publishable_key(order.currency)
    except StripeConfigError as exc:
        return render(
            request,
            'payments/order.html',
            {'order': order, 'stripe_public_key': '', 'config_error': str(exc)},
        )
    return render(
        request,
        'payments/order.html',
        {
            'order': order,
            'stripe_public_key': stripe_public_key,
            'config_error': '',
        },
    )


@require_GET
def buy_order(request, order_id: int):
    order = _get_order_or_404(order_id)
    try:
        if order.discount:
            StripeService.ensure_discount_coupon(order.discount, order.currency)
        if order.tax:
            StripeService.ensure_tax_rate(order.tax, order.currency)
        session = StripeService.create_checkout_session_for_order(order)
    except (StripeConfigError, stripe.StripeError) as exc:
        return _stripe_error_response(exc)
    return JsonResponse({'id': session.id, 'url': session.url})


@require_GET
def item_intent_page(request, item_id: int):
    item = _get_item_or_404(item_id)
    try:
        stripe_public_key = StripeService.get_publishable_key(item.currency)
    except StripeConfigError as exc:
        return render(
            request,
            'payments/item_intent.html',
            {'item': item, 'stripe_public_key': '', 'config_error': str(exc)},
        )
    return render(
        request,
        'payments/item_intent.html',
        {
            'item': item,
            'stripe_public_key': stripe_public_key,
            'config_error': '',
        },
    )


@require_GET
def buy_item_intent(request, item_id: int):
    item = _get_item_or_404(item_id)
    try:
        intent = StripeService.create_payment_intent_for_item(item)
    except (StripeConfigError, stripe.StripeError) as exc:
        return _stripe_error_response(exc)
    return JsonResponse({'clientSecret': intent.client_secret})


@require_GET
def buy_order_intent(request, order_id: int):
    order = _get_order_or_404(order_id)
    try:
        intent = StripeService.create_payment_intent_for_order(order)
    except (StripeConfigError, stripe.StripeError) as exc:
        return _stripe_error_response(exc)
    return JsonResponse({'clientSecret': intent.client_secret})
