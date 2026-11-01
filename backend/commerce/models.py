import uuid
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class Category(models.Model):
    name=models.CharField(max_length=100,unique=True); slug=models.SlugField(unique=True); icon=models.CharField(max_length=30,blank=True)
    def __str__(self): return self.name
class Business(models.Model):
    class Verification(models.TextChoices): PENDING='pending'; VERIFIED='verified'; REJECTED='rejected'
    class TaxRegistration(models.TextChoices): UNKNOWN='unknown'; NOT_REGISTERED='not_registered'; VAT_REGISTERED='vat_registered'
    class EBMStatus(models.TextChoices): NOT_CONFIGURED='not_configured'; PENDING='pending'; CERTIFIED='certified'
    class EBMSolution(models.TextChoices): NONE='none'; EBM_2_1='ebm_2_1'; ONLINE='online'; VSDC='vsdc'
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='businesses'); name=models.CharField(max_length=180); slug=models.SlugField(unique=True); description=models.TextField(blank=True); category=models.ForeignKey(Category,on_delete=models.PROTECT,related_name='businesses',null=True); district=models.CharField(max_length=100); sector=models.CharField(max_length=100,blank=True); phone=models.CharField(max_length=30); email=models.EmailField(blank=True); address=models.CharField(max_length=240,blank=True); verification_status=models.CharField(max_length=12,choices=Verification.choices,default=Verification.PENDING); review_notes=models.TextField(blank=True); is_demo=models.BooleanField(default=False,editable=False); tax_registration=models.CharField(max_length=20,choices=TaxRegistration.choices,default=TaxRegistration.UNKNOWN); vat_tin=models.CharField(max_length=20,blank=True); prices_include_vat=models.BooleanField(default=True); ebm_status=models.CharField(max_length=20,choices=EBMStatus.choices,default=EBMStatus.NOT_CONFIGURED); ebm_solution=models.CharField(max_length=12,choices=EBMSolution.choices,default=EBMSolution.NONE); ebm_approval_reference=models.CharField(max_length=80,blank=True); ebm_machine_code=models.CharField(max_length=40,blank=True); ebm_sdc_id=models.CharField(max_length=40,blank=True); cash_enabled=models.BooleanField(default=True); mobile_money_enabled=models.BooleanField(default=False); active=models.BooleanField(default=True); created_at=models.DateTimeField(auto_now_add=True)
    def clean(self):
        super().clean()
        if self.tax_registration==self.TaxRegistration.VAT_REGISTERED and not self.vat_tin.strip():
            raise ValidationError({'vat_tin':'A VAT registered business must provide its TIN.'})
        if self.ebm_status==self.EBMStatus.CERTIFIED:
            required=[('ebm_solution',self.ebm_solution),('ebm_approval_reference',self.ebm_approval_reference)]
            if self.ebm_solution==self.EBMSolution.VSDC: required.extend([('ebm_machine_code',self.ebm_machine_code),('ebm_sdc_id',self.ebm_sdc_id)])
            missing=[field for field,value in required if not value or value=='none']
            if missing: raise ValidationError({field:'Required for a certified EBM integration.' for field in missing})
    def __str__(self): return self.name
class BusinessMembership(models.Model):
    business=models.ForeignKey(Business,on_delete=models.CASCADE,related_name='members'); user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE); role=models.CharField(max_length=20,choices=[('owner','Owner'),('manager','Manager'),('staff','Staff')]); active=models.BooleanField(default=True)
    class Meta: unique_together=[('business','user')]
class BusinessVerification(models.Model):
    class DocumentType(models.TextChoices): RDB_REGISTRATION='rdb_registration'; TIN_CERTIFICATE='tin_certificate'; VAT_CERTIFICATE='vat_certificate'; OWNER_ID='owner_id'; EBM_APPROVAL='ebm_approval'; EBM_COMMITMENT='ebm_commitment'; OTHER='other'
    class Status(models.TextChoices): PENDING='pending'; APPROVED='approved'; REJECTED='rejected'
    business=models.ForeignKey(Business,on_delete=models.CASCADE,related_name='verification_documents'); document_type=models.CharField(max_length=60,choices=DocumentType.choices); document=models.FileField(upload_to='verification/'); status=models.CharField(max_length=12,choices=Status.choices,default=Status.PENDING); reviewed_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='reviewed_business_documents'); reviewed_at=models.DateTimeField(null=True,blank=True)
class Product(models.Model):
    class VATCategory(models.TextChoices): STANDARD='standard'; ZERO_RATED='zero_rated'; EXEMPT='exempt'
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); business=models.ForeignKey(Business,on_delete=models.CASCADE,related_name='products'); category=models.ForeignKey(Category,on_delete=models.PROTECT,related_name='products'); name=models.CharField(max_length=180); description=models.TextField(blank=True); price=models.DecimalField(max_digits=12,decimal_places=2,validators=[MinValueValidator(0)]); price_per_kg=models.DecimalField(max_digits=12,decimal_places=2,validators=[MinValueValidator(0)],null=True,blank=True); vat_category=models.CharField(max_length=12,choices=VATCategory.choices,default=VATCategory.STANDARD); stock=models.PositiveIntegerField(default=0); image_url=models.URLField(blank=True); image_file=models.FileField(upload_to='products/images/',blank=True,null=True); video_file=models.FileField(upload_to='products/videos/',blank=True,null=True); active=models.BooleanField(default=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: indexes=[models.Index(fields=['active','category']),models.Index(fields=['name'])]
class InventoryMovement(models.Model):
    product=models.ForeignKey(Product,on_delete=models.PROTECT,related_name='movements'); quantity_change=models.IntegerField(); reason=models.CharField(max_length=120); created_at=models.DateTimeField(auto_now_add=True)
class Address(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='addresses'); label=models.CharField(max_length=50); district=models.CharField(max_length=100); address_line=models.CharField(max_length=240); phone=models.CharField(max_length=30); is_default=models.BooleanField(default=False)
class Order(models.Model):
    class Status(models.TextChoices): PENDING='pending'; ACCEPTED='accepted'; REJECTED='rejected'; FULFILLING='fulfilling'; DELIVERED='delivered'; CANCELLED='cancelled'
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); reference=models.CharField(max_length=20,unique=True); customer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='orders'); guest_name=models.CharField(max_length=120,blank=True); guest_email=models.EmailField(blank=True); guest_phone=models.CharField(max_length=30,blank=True); status=models.CharField(max_length=15,choices=Status.choices,default='pending'); payment_method=models.CharField(max_length=20,default='cash'); subtotal=models.DecimalField(max_digits=12,decimal_places=2); tax_total=models.DecimalField(max_digits=12,decimal_places=2,default=0); delivery_fee=models.DecimalField(max_digits=12,decimal_places=2,default=0); total=models.DecimalField(max_digits=12,decimal_places=2); delivery_address=models.CharField(max_length=300,blank=True); created_at=models.DateTimeField(auto_now_add=True)
class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items'); product=models.ForeignKey(Product,on_delete=models.PROTECT,related_name='order_lines'); business=models.ForeignKey(Business,on_delete=models.PROTECT,related_name='order_lines'); product_name=models.CharField(max_length=180); unit_price=models.DecimalField(max_digits=12,decimal_places=2); price_per_kg=models.DecimalField(max_digits=12,decimal_places=2,null=True,blank=True); quantity=models.PositiveIntegerField(validators=[MinValueValidator(1)]); line_total=models.DecimalField(max_digits=12,decimal_places=2); vat_category=models.CharField(max_length=12,choices=Product.VATCategory.choices,default=Product.VATCategory.STANDARD); vat_rate=models.DecimalField(max_digits=5,decimal_places=2,default=0); vat_amount=models.DecimalField(max_digits=12,decimal_places=2,default=0); vat_included=models.BooleanField(default=True)
class OrderReceiptDelivery(models.Model):
    class Channel(models.TextChoices): EMAIL='email'; SMS='sms'
    class Status(models.TextChoices): SENT='sent'; PREVIEW='preview'; FAILED='failed'; NOT_CONFIGURED='not_configured'
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='receipt_deliveries'); channel=models.CharField(max_length=8,choices=Channel.choices); recipient=models.CharField(max_length=254,blank=True); status=models.CharField(max_length=20,choices=Status.choices); provider_reference=models.CharField(max_length=120,blank=True); error_message=models.CharField(max_length=300,blank=True); sent_at=models.DateTimeField(null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['created_at']; indexes=[models.Index(fields=['order','channel'])]
class Payment(models.Model):
    class Status(models.TextChoices): PENDING='pending'; SUCCEEDED='succeeded'; FAILED='failed'; REFUNDED='refunded'
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); order=models.ForeignKey(Order,on_delete=models.PROTECT,related_name='payments'); provider=models.CharField(max_length=32); provider_reference=models.CharField(max_length=120,blank=True); amount=models.DecimalField(max_digits=12,decimal_places=2); status=models.CharField(max_length=12,choices=Status.choices,default=Status.PENDING); idempotency_key=models.CharField(max_length=120,unique=True); created_at=models.DateTimeField(auto_now_add=True)
class Refund(models.Model):
    payment=models.ForeignKey(Payment,on_delete=models.PROTECT,related_name='refunds'); amount=models.DecimalField(max_digits=12,decimal_places=2); status=models.CharField(max_length=20,default='requested'); reason=models.TextField(blank=True); created_at=models.DateTimeField(auto_now_add=True)
class Service(models.Model):
    business=models.ForeignKey(Business,on_delete=models.CASCADE,related_name='services'); name=models.CharField(max_length=160); description=models.TextField(blank=True); price=models.DecimalField(max_digits=12,decimal_places=2); vat_category=models.CharField(max_length=12,choices=Product.VATCategory.choices,default=Product.VATCategory.STANDARD); capacity=models.PositiveIntegerField(default=1); active=models.BooleanField(default=True)
class BusinessAvailability(models.Model):
    business=models.ForeignKey(Business,on_delete=models.CASCADE,related_name='availability'); weekday=models.PositiveSmallIntegerField(validators=[MaxValueValidator(6)]); start_time=models.TimeField(); end_time=models.TimeField(); capacity=models.PositiveIntegerField(default=1)
class Booking(models.Model):
    class Status(models.TextChoices): PENDING='pending'; CONFIRMED='confirmed'; REJECTED='rejected'; CANCELLED='cancelled'; COMPLETED='completed'
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); reference=models.CharField(max_length=20,unique=True); service=models.ForeignKey(Service,on_delete=models.PROTECT,related_name='bookings'); customer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True); guest_name=models.CharField(max_length=120,blank=True); guest_phone=models.CharField(max_length=30,blank=True); starts_at=models.DateTimeField(); ends_at=models.DateTimeField(); party_size=models.PositiveIntegerField(default=1); unit_price=models.DecimalField(max_digits=12,decimal_places=2,default=0); subtotal=models.DecimalField(max_digits=12,decimal_places=2,default=0); vat_category=models.CharField(max_length=12,choices=Product.VATCategory.choices,default=Product.VATCategory.STANDARD); vat_rate=models.DecimalField(max_digits=5,decimal_places=2,default=0); vat_amount=models.DecimalField(max_digits=12,decimal_places=2,default=0); vat_included=models.BooleanField(default=True); total=models.DecimalField(max_digits=12,decimal_places=2,default=0); notes=models.TextField(blank=True); status=models.CharField(max_length=12,choices=Status.choices,default=Status.PENDING); created_at=models.DateTimeField(auto_now_add=True)
class Review(models.Model):
    business=models.ForeignKey(Business,on_delete=models.CASCADE,related_name='reviews'); customer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE); order=models.ForeignKey(Order,on_delete=models.PROTECT,null=True,blank=True); rating=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)]); body=models.TextField(blank=True); approved=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
class Favorite(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE); business=models.ForeignKey(Business,on_delete=models.CASCADE,null=True,blank=True); product=models.ForeignKey(Product,on_delete=models.CASCADE,null=True,blank=True)
    class Meta: constraints=[models.CheckConstraint(condition=(models.Q(business__isnull=False,product__isnull=True)|models.Q(business__isnull=True,product__isnull=False)),name='favorite_one_target')]
class Notification(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='notifications'); title=models.CharField(max_length=180); body=models.TextField(); read_at=models.DateTimeField(null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True)
class Conversation(models.Model):
    business=models.ForeignKey(Business,on_delete=models.CASCADE); customer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE); created_at=models.DateTimeField(auto_now_add=True)
class Message(models.Model):
    conversation=models.ForeignKey(Conversation,on_delete=models.CASCADE,related_name='messages'); sender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT); body=models.TextField(); created_at=models.DateTimeField(auto_now_add=True)
class Complaint(models.Model):
    business=models.ForeignKey(Business,on_delete=models.CASCADE); reporter=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT); reason=models.CharField(max_length=120); details=models.TextField(blank=True); status=models.CharField(max_length=20,default='open'); created_at=models.DateTimeField(auto_now_add=True)
class AuditLog(models.Model):
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True); action=models.CharField(max_length=120); object_type=models.CharField(max_length=80); object_id=models.CharField(max_length=80); detail=models.JSONField(default=dict); created_at=models.DateTimeField(auto_now_add=True)
