from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Address, Business, Category, Complaint, Conversation, Favorite, Notification, Order, Payment, Product

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

class GuidanceApiTests(TestCase):
 def setUp(self):
  self.client=APIClient()
 def test_guidance_fallback_is_public_multilingual_and_validates_input(self):
  response=self.client.post('/api/ai-guidance/',{'question':'How do I verify my business?','language':'en','context':'general'},format='json')
  self.assertEqual(response.status_code,200)
  self.assertEqual(response.data['provider'],'guidance_fallback')
  self.assertEqual(response.data['topic'],'verification')
  self.assertIn('Business registration',response.data['answer'])
  rw=self.client.post('/api/ai-guidance/',{'question':'Nigute nandikisha ubucuruzi?','language':'rw'},format='json')
  self.assertEqual(rw.status_code,200)
  self.assertEqual(rw.data['language'],'rw')
  invalid=self.client.post('/api/ai-guidance/',{'question':'hi'},format='json')
  self.assertEqual(invalid.status_code,400)

class MobileMoneyEscrowTests(TestCase):
 def setUp(self):
  self.client=APIClient()
  owner=get_user_model().objects.create_user(username='escrow-owner',password='Secure-test-password-123')
  category=Category.objects.create(name='Escrow',slug='escrow')
  business=Business.objects.create(owner=owner,name='Escrow Shop',slug='escrow-shop',category=category,district='Kigali',phone='+250788000001',verification_status=Business.Verification.VERIFIED,active=True)
  product=Product.objects.create(business=business,category=category,name='Held product',price=Decimal('10000.00'),stock=5)
  response=self.client.post('/api/orders/',{'items':[{'product_id':str(product.pk),'quantity':1}],'payment_method':'mtn_momo','guest_name':'Buyer','guest_phone':'250788000002'},format='json')
  self.order=Order.objects.get(pk=response.data['id'])
  self.payment=Payment.objects.get(order=self.order)

 def test_webhook_requires_signature(self):
  response=self.client.post('/api/payments/webhook/',{'provider':'mtn_momo','provider_reference':'unknown','status':'success'},format='json')
  self.assertEqual(response.status_code,503)

 def test_wrong_receipt_pin_does_not_release_funds(self):
  self.payment.status=Payment.Status.SUCCEEDED
  self.payment.escrow_status=Payment.EscrowStatus.HELD
  self.payment.confirmation_pin_hash='pbkdf2_sha256$260000$salt$invalid'
  self.payment.save(update_fields=['status','escrow_status','confirmation_pin_hash'])
  response=self.client.post(f'/api/orders/{self.order.pk}/confirm-receipt/',{'phone':'250788000002','pin':'123456'},format='json')
  self.assertEqual(response.status_code,401)
  self.payment.refresh_from_db()
  self.assertEqual(self.payment.escrow_status,Payment.EscrowStatus.HELD)

class MarketplaceAccountServiceTests(TestCase):
 def setUp(self):
  self.owner=get_user_model().objects.create_user(username='service-owner',password='Secure-test-password-123')
  self.customer=get_user_model().objects.create_user(username='service-customer',password='Secure-test-password-123')
  self.other=get_user_model().objects.create_user(username='service-other',password='Secure-test-password-123')
  self.category=Category.objects.create(name='Services',slug='services')
  self.business=Business.objects.create(owner=self.owner,name='Service Shop',slug='service-shop',category=self.category,district='Kigali',phone='+250111111111',verification_status=Business.Verification.VERIFIED,active=True)
  self.client=APIClient(); self.client.force_authenticate(self.customer)

 def test_address_is_private_and_default_is_enforced(self):
  first=self.client.post('/api/addresses/',{'label':'Home','district':'Gasabo','address_line':'KG 1 Ave','phone':'250788000001','is_default':True},format='json')
  second=self.client.post('/api/addresses/',{'label':'Work','district':'Kicukiro','address_line':'KK 2 Ave','phone':'250788000002','is_default':True},format='json')
  self.assertEqual(first.status_code,201); self.assertEqual(second.status_code,201)
  self.assertEqual(Address.objects.filter(user=self.customer,is_default=True).count(),1)
  self.other_client=APIClient(); self.other_client.force_authenticate(self.other)
  self.assertEqual(self.other_client.get('/api/addresses/').data,[])

 def test_favorite_notification_complaint_and_conversation_are_scoped(self):
  favorite=self.client.post('/api/favorites/',{'business':str(self.business.pk),'product':None},format='json')
  self.assertEqual(favorite.status_code,201)
  complaint=self.client.post('/api/complaints/',{'business':str(self.business.pk),'reason':'Service quality','details':'Please review this listing.'},format='json')
  self.assertEqual(complaint.status_code,201)
  Notification.objects.create(user=self.customer,title='Order update',body='Your order was accepted.')
  unread=self.client.get('/api/notifications/').data
  self.assertEqual(len(unread),1)
  self.assertEqual(self.client.post('/api/notifications/'+str(unread[0]['id'])+'/read/',{},format='json').status_code,200)
  conversation=self.client.post('/api/conversations/',{'business':str(self.business.pk),'message':'Hello, is this item available?'},format='json')
  self.assertEqual(conversation.status_code,201)
  sent=self.client.post('/api/conversations/'+str(conversation.data['id'])+'/send/',{'body':'Could you confirm delivery?'},format='json')
  self.assertEqual(sent.status_code,201)
  self.assertEqual(Complaint.objects.filter(reporter=self.customer).count(),1)
  self.assertEqual(Favorite.objects.filter(user=self.customer).count(),1)
  self.assertEqual(Conversation.objects.filter(customer=self.customer).count(),1)
