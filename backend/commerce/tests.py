from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Business, Category, Order, Product

class MarketplaceOrderTests(TestCase):
 def setUp(self):
  user=get_user_model().objects.create_user(username='maker',password='Secure-test-password-123')
  category=Category.objects.create(name='Home',slug='home')
  business=Business.objects.create(owner=user,name='Demo baskets',slug='demo-baskets',category=category,district='Kigali',phone='+250000000000',verification_status=Business.Verification.VERIFIED)
  self.product=Product.objects.create(business=business,category=category,name='Basket',price=Decimal('28500.00'),stock=3)
  self.client=APIClient()
 def test_guest_order_uses_server_price_and_saves_snapshot(self):
  response=self.client.post('/api/orders/',{'items':[{'product_id':str(self.product.pk),'quantity':2}],'payment_method':'cash','guest_name':'Guest'},format='json')
  self.assertEqual(response.status_code,201)
  order=Order.objects.get(reference=response.data['reference'])
  self.assertEqual(order.total,Decimal('57000.00'))
  line=order.items.get()
  self.assertEqual((line.product_name,line.unit_price,line.quantity),('Basket',Decimal('28500.00'),2))
  self.product.refresh_from_db(); self.assertEqual(self.product.stock,1)
 def test_insufficient_stock_does_not_create_order_or_decrement(self):
  response=self.client.post('/api/orders/',{'items':[{'product_id':str(self.product.pk),'quantity':4}],'payment_method':'cash'},format='json')
  self.assertEqual(response.status_code,409)
  self.assertEqual(Order.objects.count(),0)
  self.product.refresh_from_db(); self.assertEqual(self.product.stock,3)
 def test_customer_order_history_is_private(self):
  response=self.client.post('/api/orders/',{'items':[{'product_id':str(self.product.pk),'quantity':1}],'payment_method':'cash'},format='json')
  order_id=response.data['id']
  self.assertEqual(len(self.client.get('/api/orders/').data),0)
  customer=get_user_model().objects.create_user(username='customer',password='Secure-test-password-123')
  self.client.force_authenticate(customer)
  self.assertEqual(len(self.client.get('/api/orders/').data),0)
  self.assertEqual(Order.objects.filter(pk=order_id).count(),1)
