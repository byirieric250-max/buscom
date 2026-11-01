from rest_framework import serializers
from .models import Business, Category, Product, Order, OrderItem, Booking, Service, Review
class CategorySerializer(serializers.ModelSerializer):
 class Meta: model=Category; fields='__all__'
class BusinessSerializer(serializers.ModelSerializer):
 category_name=serializers.CharField(source='category.name',read_only=True)
 class Meta: model=Business; fields=['id','name','slug','description','category','category_name','district','sector','phone','email','address','verification_status','tax_registration','prices_include_vat','created_at']
class ProductSerializer(serializers.ModelSerializer):
 business_name=serializers.CharField(source='business.name',read_only=True); business_slug=serializers.CharField(source='business.slug',read_only=True); district=serializers.CharField(source='business.district',read_only=True); category_name=serializers.CharField(source='category.name',read_only=True)
 business_tax_registration=serializers.CharField(source='business.tax_registration',read_only=True); prices_include_vat=serializers.BooleanField(source='business.prices_include_vat',read_only=True)
 class Meta: model=Product; fields=['id','business','business_name','business_slug','category','category_name','name','description','price','price_per_kg','vat_category','business_tax_registration','prices_include_vat','stock','image_url','image_file','video_file','active','district','created_at']
 def validate_image_file(self,uploaded):
  if uploaded is None: return uploaded
  if uploaded.size>20*1024*1024: raise serializers.ValidationError('Product images must be 20 MB or smaller.')
  head=uploaded.read(16); uploaded.seek(0)
  valid=head.startswith((b'\xff\xd8\xff',b'\x89PNG\r\n\x1a\n')) or (head[:4]==b'RIFF' and head[8:12]==b'WEBP')
  if not valid: raise serializers.ValidationError('Upload a valid JPG, PNG, or WebP image.')
  return uploaded
 def validate_video_file(self,uploaded):
  if uploaded is None: return uploaded
  if uploaded.size>100*1024*1024: raise serializers.ValidationError('Product videos must be 100 MB or smaller.')
  head=uploaded.read(16); uploaded.seek(0)
  valid=head.startswith(b'\x1a\x45\xdf\xa3') or (len(head)>=12 and head[4:8]==b'ftyp')
  if not valid: raise serializers.ValidationError('Upload a valid MP4, MOV, or WebM video.')
  return uploaded
class OrderItemSerializer(serializers.ModelSerializer):
 class Meta: model=OrderItem; fields=['product','product_name','unit_price','price_per_kg','quantity','line_total','vat_category','vat_rate','vat_amount','vat_included','business']
class OrderSerializer(serializers.ModelSerializer):
 items=OrderItemSerializer(many=True,read_only=True)
 class Meta: model=Order; fields=['id','reference','status','payment_method','subtotal','tax_total','delivery_fee','total','items','created_at']
class BookingSerializer(serializers.ModelSerializer):
 business_name=serializers.CharField(source='service.business.name',read_only=True); service_name=serializers.CharField(source='service.name',read_only=True)
 class Meta: model=Booking; fields=['id','reference','service','service_name','business_name','starts_at','ends_at','party_size','unit_price','subtotal','vat_category','vat_rate','vat_amount','vat_included','total','notes','status','created_at']; read_only_fields=['id','reference','unit_price','subtotal','vat_category','vat_rate','vat_amount','vat_included','total','status','created_at']
class ServiceSerializer(serializers.ModelSerializer):
 business_name=serializers.CharField(source='business.name',read_only=True); business_id=serializers.UUIDField(read_only=True); business_tax_registration=serializers.CharField(source='business.tax_registration',read_only=True); prices_include_vat=serializers.BooleanField(source='business.prices_include_vat',read_only=True)
 class Meta: model=Service; fields=['id','business','business_id','business_name','business_tax_registration','prices_include_vat','name','description','price','vat_category','capacity','active']
class ReviewSerializer(serializers.ModelSerializer):
 customer_name=serializers.CharField(source='customer.first_name',read_only=True)
 class Meta:
  model=Review; fields=['id','business','customer_name','order','rating','body','created_at']; read_only_fields=['id','customer_name','created_at']
