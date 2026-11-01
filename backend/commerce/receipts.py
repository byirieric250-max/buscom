import json
from decimal import Decimal
from html import escape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from .models import Order, OrderReceiptDelivery, Payment


def _rwf(value):
    return f"RWF {Decimal(value):,.0f}"


def _receipt_content(order):
    items = list(order.items.all())
    rows = [
        f"{item.quantity} x {item.product_name} — {_rwf(item.unit_price)} each; line total {_rwf(item.line_total)}"
        for item in items
    ]
    payments = list(order.payments.all())
    paid = sum((payment.amount for payment in payments if payment.status == Payment.Status.SUCCEEDED), Decimal('0.00'))
    if order.payment_method in ['cash', 'cash_on_delivery']:
        payment_detail = f"Payment method: Cash on delivery\nAmount paid: {_rwf(paid)}\nAmount due: {_rwf(order.total - paid)}"
    elif paid:
        payment_detail = f"Payment method: {order.payment_method}\nAmount paid: {_rwf(paid)}\nAmount due: {_rwf(max(order.total - paid, Decimal('0.00')))}"
    else:
        payment_detail = f"Payment method: {order.payment_method}\nPayment status: Awaiting provider confirmation\nAmount paid: {_rwf(0)}\nAmount due: {_rwf(order.total)}"

    buyer = order.guest_name or (order.customer.get_full_name() if order.customer_id else '') or 'Customer'
    text_items = '\n'.join(f"• {row}" for row in rows)
    text_body = (
        f"Hello {buyer},\n\nWe received your Imena order {order.reference}.\n\n"
        f"Items:\n{text_items}\n\nSubtotal: {_rwf(order.subtotal)}\nVAT total: {_rwf(order.tax_total)}\n"
        f"Delivery fee: {_rwf(order.delivery_fee)}\nTotal: {_rwf(order.total)}\n"
        f"{payment_detail}\n\nOrder status: {order.status}\n"
        "Keep your order reference and phone number to track this order."
    )
    html_rows = ''.join(
        '<tr>'
        f'<td>{escape(item.product_name)}</td><td>{item.quantity}</td>'
        f'<td>{escape(_rwf(item.unit_price))}</td><td>{escape(_rwf(item.line_total))}</td>'
        f'<td>{escape(str(item.vat_rate))}% ({escape(_rwf(item.vat_amount))})</td>'
        '</tr>' for item in items
    )
    html_body = (
        f'<p>Hello {escape(buyer)},</p><p>We received your Imena order '
        f'<strong>{escape(order.reference)}</strong>.</p>'
        '<table><thead><tr><th>Item</th><th>Qty</th><th>Unit price</th><th>Line total</th><th>VAT</th></tr></thead>'
        f'<tbody>{html_rows}</tbody></table>'
        f'<p>Subtotal: {escape(_rwf(order.subtotal))}<br>VAT total: {escape(_rwf(order.tax_total))}<br>'
        f'Delivery fee: {escape(_rwf(order.delivery_fee))}<br>'
        f'<strong>Total: {escape(_rwf(order.total))}</strong></p>'
        f'<p>{escape(payment_detail).replace(chr(10), "<br>")}<br>Order status: {escape(order.status)}</p>'
        '<p>Keep your order reference and phone number to track this order.</p>'
    )
    return text_body, html_body


def _send_email(order, recipient, text_body, html_body):
    delivery = OrderReceiptDelivery.objects.create(
        order=order, channel=OrderReceiptDelivery.Channel.EMAIL, recipient=recipient,
        status=OrderReceiptDelivery.Status.NOT_CONFIGURED,
    )
    if not recipient:
        delivery.error_message = 'Buyer email was not provided.'
        delivery.save(update_fields=['error_message'])
        return delivery
    try:
        message = EmailMultiAlternatives(
            subject=f"Imena order {order.reference} receipt",
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        message.attach_alternative(html_body, 'text/html')
        accepted = message.send(fail_silently=False)
        if settings.EMAIL_BACKEND.endswith('console.EmailBackend'):
            delivery.status = OrderReceiptDelivery.Status.PREVIEW
            delivery.error_message = 'Printed to the API console; configure SMTP to deliver email.'
        elif accepted:
            delivery.status = OrderReceiptDelivery.Status.SENT
            delivery.sent_at = timezone.now()
        else:
            delivery.status = OrderReceiptDelivery.Status.FAILED
            delivery.error_message = 'Email backend did not accept the receipt.'
    except Exception as exc:
        delivery.status = OrderReceiptDelivery.Status.FAILED
        delivery.error_message = str(exc)[:300]
    delivery.save(update_fields=['status', 'sent_at', 'error_message'])
    return delivery


def _send_sms(order, recipient, text_body):
    delivery = OrderReceiptDelivery.objects.create(
        order=order, channel=OrderReceiptDelivery.Channel.SMS, recipient=recipient,
        status=OrderReceiptDelivery.Status.NOT_CONFIGURED,
    )
    if not recipient:
        delivery.error_message = 'Buyer phone number was not provided.'
        delivery.save(update_fields=['error_message'])
        return delivery
    if not settings.SMS_GATEWAY_URL:
        delivery.error_message = 'Configure SMS_GATEWAY_URL to deliver text messages.'
        delivery.save(update_fields=['error_message'])
        return delivery
    payload = json.dumps({'to': recipient, 'from': settings.SMS_SENDER_ID, 'message': text_body}).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    if settings.SMS_GATEWAY_TOKEN:
        headers['Authorization'] = f'Bearer {settings.SMS_GATEWAY_TOKEN}'
    try:
        request = Request(settings.SMS_GATEWAY_URL, data=payload, headers=headers, method='POST')
        with urlopen(request, timeout=10) as response:
            if 200 <= response.status < 300:
                delivery.status = OrderReceiptDelivery.Status.SENT
                delivery.sent_at = timezone.now()
            else:
                delivery.status = OrderReceiptDelivery.Status.FAILED
                delivery.error_message = f'SMS gateway returned HTTP {response.status}.'
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        delivery.status = OrderReceiptDelivery.Status.FAILED
        delivery.error_message = str(exc)[:300]
    delivery.save(update_fields=['status', 'sent_at', 'error_message'])
    return delivery


def send_order_receipt(order_id):
    """Send the order receipt to the buyer, recording each channel outcome."""
    try:
        order = Order.objects.select_related('customer').prefetch_related('items', 'payments').get(pk=order_id)
        text_body, html_body = _receipt_content(order)
        email = order.guest_email or (order.customer.email if order.customer_id else '')
        _send_email(order, email, text_body, html_body)
        _send_sms(order, order.guest_phone, text_body)
    except Exception:
        # Receipt delivery must not undo a committed stock/order transaction.
        return
