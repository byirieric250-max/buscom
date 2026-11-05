import json
import os
import secrets
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError
import mimetypes
from pathlib import Path
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import FileResponse, Http404
from django.db.models import Case, Count, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from .models import Address, AuditLog, Booking, Business, BusinessVerification, Category, Complaint, Conversation, Favorite, InventoryMovement, Message, Notification, Order, OrderItem, Payment, Product, Review, Service
from .serializers import AddressSerializer, BookingSerializer, BusinessSerializer, CategorySerializer, ComplaintSerializer, ConversationSerializer, FavoriteSerializer, NotificationSerializer, OrderSerializer, ProductSerializer, ReviewSerializer, ServiceSerializer
from .receipts import send_order_receipt

class HealthView(APIView):
 permission_classes=[AllowAny]
 def get(self,request): return Response({'status':'ok','service':'Imena Rwanda Commerce API'})

class GuidanceView(APIView):
 permission_classes=[AllowAny]
 def post(self,request):
  question=str(request.data.get('question','')).strip()
  language=str(request.data.get('language','en')).lower()
  context=str(request.data.get('context','general')).strip().lower()
  if len(question)<3 or len(question)>500:
   return Response({'detail':'Ask a question between 3 and 500 characters.'},status=400)
  language='rw' if language in ('rw','kinyarwanda') else 'fr' if language=='fr' or language.startswith('fran') else 'sw' if language=='sw' else 'en'
  guides={
   'en':{
    'verification':'Business registration: 1. Prepare your RDB registration, TIN, and owner ID or passport. 2. Submit the business application and supporting PDF/JPG/PNG documents. 3. An administrator reviews the application. 4. A listing is public only within its approval rules. Do not treat a submitted application as approval.',
    'vat':'VAT steps: 1. Confirm whether your business is VAT registered. 2. Enter the TIN and tax registration details. 3. Upload valid supporting documents. 4. Confirm the correct VAT category. The platform calculates VAT but cannot replace advice from RRA or a tax professional.',
    'payment':'Payment safety: 1. Choose an enabled payment method. 2. Do not send payment outside the checkout flow. 3. A reference entered by a customer is not provider proof. 4. Treat a payment as confirmed only after a trusted server-side provider response.',
    'booking':'Booking steps: 1. Choose the service and date. 2. Check availability and remaining capacity. 3. Submit guest details and keep the booking reference. 4. Contact the business to change or cancel it.',
    'order':'Order steps: 1. Review the listing and quantity. 2. Enter delivery details. 3. Verify the server-calculated total. 4. Keep your order reference. 5. Tracking shows only the status confirmed by the platform.',
    'general':'Choose a category and review a listing, then check its price, availability, and delivery details before ordering or booking. Confirm important legal, tax, registration, or payment decisions with the relevant Rwandan authority.'
   },
   'rw':{
    'verification':'Kwiyandikisha: 1. Tegura RDB, TIN, n’indangamuntu cyangwa pasiporo. 2. Ohereza form n’inyandiko za PDF/JPG/PNG. 3. Umuyobozi agenzura dosiye. 4. Ntukite ubucuruzi bwemejwe imbere yuko busuzumwa kandi bwemezwa.',
    'vat':'Intambwe za VAT: 1. Menya niba ubucuruzi buri muri VAT. 2. Andika TIN n’amakuru y’imisoro. 3. Ohereza inyandiko zemewe. 4. Hitamo icyiciro cya VAT gikwiye. Baza RRA cyangwa umuhanga mu misoro ku byemezo.',
    'payment':'Umutekano w’ishyura: 1. Hitamo uburyo bwo kwishyura bwerekanwe. 2. Ntuzishyure hanze ya sisitemu. 3. Nomero yandinzwe ntiyemeza ko byishyuwe. 4. Icyemezo gitangwa gusa na provider yizerwa ku seriveri.',
    'booking':'Kubika: 1. Hitamo serivisi n’itariki. 2. Reba umwanya. 3. Ohereza amakuru kandi ubike numero y’icyemezo. 4. Saba guhindura cyangwa guhagarika ku bucuruzi.',
    'order':'Gutumiza: 1. Reba igicuruzwa n’ingano. 2. Andika aho byoherezwa. 3. Reba igiciro cyabazwe na serveri. 4. Bika numero y’ituma. 5. Kurikirana uko itumanaho ryemejwe.',
    'general':'Hitamo icyiciro, reba ubucuruzi, igiciro n’aho bishobora kuba, nyuma utumize cyangwa ubike. Amategeko n’imisoro bishobora guhinduka; baza inzego z’U Rwanda zibishinzwe.'
   },
   'sw':{
    'verification':'Hatua za usajili: 1. Andaa RDB, TIN, kitambulisho au pasipoti. 2. Wasilisha fomu na hati za PDF/JPG/PNG. 3. Msimamizi hukagua hati. 4. Orodha haithibitiki hadi idhini itolewe.',
    'vat':'Hatua za VAT: 1. Hakikisha biashara yako imesajiliwa kwa VAT. 2. Weka TIN na taarifa za kodi. 3. Pakia hati sahihi. 4. Chagua kiwango cha VAT. Hakiki sheria na RRA au mtaalamu wa kodi.',
    'payment':'Usalama wa malipo: 1. Chagua njia iliyowezeshwa. 2. Usilipa nje ya mfumo. 3. Rejea ya mteja si uthibitisho wa mtoa huduma. 4. Malipo yanathibitishwa tu na majibu ya mtoa huduma yaliyotumwa na seva.',
    'booking':'Hatua za kuhifadhi: 1. Chagua huduma na tarehe. 2. Angalia nafasi. 3. Tuma maelezo na hifadhi rejea. 4. Wasiliana ili kubadilisha au kughairi.',
    'order':'Hatua za kuagiza: 1. Angalia bidhaa na kiasi. 2. Weka anwani ya utoaji. 3. Hakiki jumla iliyokokotwa na seva. 4. Hifadhi rejea ya agizo. 5. Hali inaonekana tu ikiwa imethibitishwa na mfumo.',
    'general':'Chagua aina, kagua biashara, bei na upatikanaji, kisha tuma agizo au uhifadhi. Kwa maamuzi muhimu ya sheria, kodi au malipo, thibitisha na mamlaka husika ya Rwanda.'
   },
   'fr':{
    'verification':'Inscription : 1. Préparez la RDB, le TIN et une pièce d’identité ou passeport. 2. Envoyez la demande avec des PDF/JPG/PNG valides. 3. Un administrateur examine le dossier. 4. Une inscription n’est approuvée qu’après validation officielle.',
    'vat':'Étapes TVA : 1. Vérifiez l’enregistrement TVA. 2. Indiquez le TIN et les renseignements fiscaux. 3. Téléversez les justificatifs. 4. Choisissez le bon taux TVA. Demandez conseil à l’administration fiscale ou à un professionnel.',
    'payment':'Sécurité du paiement : 1. Choisissez une méthode activée. 2. Ne payez jamais hors du site. 3. Une référence saisie ne prouve pas le paiement. 4. Un paiement est confirmé uniquement par une réponse fiable du fournisseur côté serveur.',
    'booking':'Étapes de réservation : 1. Choisissez le service et la date. 2. Vérifiez les places disponibles. 3. Envoyez vos coordonnées et conservez la référence. 4. Contactez l’entreprise pour modifier ou annuler.',
    'order':'Étapes de commande : 1. Vérifiez l’article et la quantité. 2. Indiquez la livraison. 3. Vérifiez le total calculé par le serveur. 4. Conservez la référence. 5. Suivez uniquement le statut confirmé par la plateforme.',
    'general':'Choisissez une catégorie, consultez une entreprise, puis vérifiez le prix, la disponibilité et la livraison avant de commander ou réserver. Confirmez les décisions légales ou fiscales auprès de l’autorité rwandaise compétente.'
   }
  }
  text=question.lower()
  topic='verification' if any(w in text for w in ('register','registration','verify','verification','rdb','kwiyandikisha','usajili','inscription')) else 'vat' if any(w in text for w in ('vat','tax','rra','tin','imisoro','tva')) else 'payment' if any(w in text for w in ('pay','payment','momo','airtel','refund','ishyura','malipo')) else 'booking' if any(w in text for w in ('book','booking','reservation','kubika','hifadhi')) else 'order' if any(w in text for w in ('order','checkout','delivery','stock','ituma','agizo','commande')) else context if context in guides[language] else 'general'
  fallback=guides[language][topic]
  api_url=os.getenv('AI_GUIDANCE_API_URL','').strip(); api_key=os.getenv('AI_GUIDANCE_API_KEY','').strip(); model=os.getenv('AI_GUIDANCE_MODEL','gpt-4o-mini').strip()
  if api_url and api_key:
   payload=json.dumps({'model':model,'messages':[{'role':'system','content':'Translate Rwanda commerce and regulatory steps into clear numbered instructions. Never approve businesses, taxes, or payments or invent official deadlines and fees.'},{'role':'user','content':f'Language: {language}. Context: {context}. Question: {question}. Trusted guidance: {fallback}'}],'temperature':0.2}).encode()
   req=urllib_request.Request(api_url,data=payload,headers={'Content-Type':'application/json','Authorization':f'Bearer {api_key}'},method='POST')
   try:
    with urllib_request.urlopen(req,timeout=12) as response:
     result=json.loads(response.read().decode())
    answer=result.get('choices',[{}])[0].get('message',{}).get('content','').strip()
    if answer:
     return Response({'answer':answer,'language':language,'topic':topic,'provider':'ai_configured','disclaimer':'This guidance is informational and not legal or tax advice.'})
   except (HTTPError,URLError,TimeoutError,json.JSONDecodeError,IndexError,KeyError):
    pass
  return Response({'answer':fallback,'language':language,'topic':topic,'provider':'guidance_fallback','disclaimer':'This guidance is informational and not legal or tax advice.'})
class PrivateMediaView(APIView):
 permission_classes=[IsAdminUser]
 def get(self,request,path):
  root=Path(settings.MEDIA_ROOT).resolve(); file_path=(root/path).resolve()
  if root not in file_path.parents or not file_path.is_file(): raise Http404
  return FileResponse(file_path.open('rb'),as_attachment=True,filename=file_path.name)
class ProductMediaView(APIView):
 permission_classes=[AllowAny]
 def get(self,request,path):
  relative_path=f'products/{path}'
  if not Product.objects.filter(Q(image_file=relative_path)|Q(video_file=relative_path),active=True,business__active=True).filter(Q(business__verification_status=Business.Verification.VERIFIED)|Q(business__is_demo=True)).exists(): raise Http404
  root=Path(settings.MEDIA_ROOT).resolve(); file_path=(root/relative_path).resolve()
  if root not in file_path.parents or not file_path.is_file(): raise Http404
  content_type=mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream'
  response=FileResponse(file_path.open('rb'),content_type=content_type)
  response['X-Content-Type-Options']='nosniff'
  return response
class RegisterView(APIView):
 permission_classes=[AllowAny]
 def post(self,request):
  User=get_user_model(); username=request.data.get('username') or request.data.get('email'); password=request.data.get('password'); email=request.data.get('email','')
  if not username or not password or len(password)<10: return Response({'detail':'Username and a password of at least 10 characters are required.'},status=400)
  if User.objects.filter(username=username).exists(): return Response({'detail':'An account with this username already exists.'},status=400)
  user=User.objects.create_user(username=username,email=email,password=password,first_name=request.data.get('first_name','')); token=Token.objects.create(user=user)
  return Response({'token':token.key,'user':{'id':user.pk,'username':user.username,'email':user.email}},status=201)
class LoginView(APIView):
 permission_classes=[AllowAny]
 def post(self,request):
  login_value=request.data.get('username') or request.data.get('email')
  User=get_user_model()
  matching_user=User.objects.filter(email__iexact=login_value).first() if login_value else None
  username=matching_user.username if matching_user else login_value
  user=authenticate(username=username,password=request.data.get('password'))
  if not user: return Response({'detail':'Those sign-in details did not match.'},status=400)
  token,_=Token.objects.get_or_create(user=user); return Response({'token':token.key,'user':{'id':user.pk,'username':user.username,'email':user.email,'is_staff':user.is_staff,'is_superuser':user.is_superuser}})
class MeView(APIView):
 permission_classes=[IsAuthenticated]
 def get(self,request): return Response({'id':request.user.pk,'username':request.user.username,'email':request.user.email,'is_staff':request.user.is_staff})
class LogoutView(APIView):
 permission_classes=[IsAuthenticated]
 def post(self,request):
  request.auth.delete()
  return Response({'detail':'Signed out successfully.'})
class SellerReportsView(APIView):
 permission_classes=[IsAuthenticated]
 def get(self,request):
  allowed=Business.objects.filter(Q(owner=request.user)|Q(members__user=request.user,members__active=True,members__role__in=['owner','manager'])).distinct().order_by('name')
  businesses=list(allowed.values('id','name','district','verification_status','tax_registration'))
  business_id=request.query_params.get('business')
  business=allowed.filter(pk=business_id).first() if business_id else allowed.first()
  if business_id and business is None: return Response({'detail':'That shop is not available to this account.'},status=404)
  days=int(request.query_params.get('days','30')) if request.query_params.get('days','30').isdigit() else 30
  days=days if days in [7,30,90] else 30
  if business is None:
   return Response({'businesses':businesses,'selected_business':None,'period_days':days,'summary':{'orders':0,'gross_sales':0,'delivered_sales':0,'units_sold':0,'average_order_value':0},'statuses':[],'daily_sales':[],'top_products':[],'orders':[]})
  since=timezone.now()-timedelta(days=days)
  scoped=OrderItem.objects.filter(business=business,order__created_at__gte=since).select_related('order__customer').annotate(charged_total=F('line_total')+Case(When(vat_included=False,then=F('vat_amount')),default=Value(Decimal('0.00')),output_field=DecimalField(max_digits=12,decimal_places=2)))
  placed=scoped.exclude(order__status__in=[Order.Status.CANCELLED,Order.Status.REJECTED])
  order_qs=Order.objects.filter(pk__in=scoped.values('order_id')).select_related('customer').prefetch_related('receipt_deliveries').order_by('-created_at')
  gross=placed.aggregate(value=Sum('charged_total'))['value'] or Decimal('0.00')
  delivered=placed.filter(order__status=Order.Status.DELIVERED).aggregate(value=Sum('charged_total'))['value'] or Decimal('0.00')
  units=placed.aggregate(value=Sum('quantity'))['value'] or 0
  statuses=list(order_qs.values('status').annotate(count=Count('id')).order_by('status'))
  daily=list(placed.annotate(day=TruncDate('order__created_at')).values('day').annotate(orders=Count('order_id',distinct=True),units=Sum('quantity'),gross_sales=Sum('charged_total')).order_by('day'))
  top=list(placed.values('product_name').annotate(units=Sum('quantity'),gross_sales=Sum('charged_total')).order_by('-units')[:8])
  order_rows=[]
  for order in order_qs[:100]:
   lines=list(scoped.filter(order=order).values('product_name','quantity','unit_price','line_total','vat_category','vat_rate','vat_amount','vat_included'))
   customer=order.customer
   order_rows.append({'id':str(order.pk),'reference':order.reference,'status':order.status,'created_at':order.created_at.isoformat(),'payment_method':order.payment_method,'buyer_name':order.guest_name or (customer.get_full_name() if customer else '') or (customer.username if customer else 'Guest buyer'),'buyer_email':order.guest_email or (customer.email if customer else ''),'buyer_phone':order.guest_phone,'delivery_address':order.delivery_address,'business_total':float(sum((line['charged_total'] for line in scoped.filter(order=order)),Decimal('0.00'))),'business_vat':float(sum((line['vat_amount'] for line in lines),Decimal('0.00'))),'items':[{**line,'unit_price':str(line['unit_price']),'line_total':str(line['line_total']),'vat_rate':str(line['vat_rate']),'vat_amount':str(line['vat_amount'])} for line in lines],'receipt_deliveries':[{'channel':delivery.channel,'status':delivery.status,'sent_at':delivery.sent_at.isoformat() if delivery.sent_at else None,'error_message':delivery.error_message} for delivery in order.receipt_deliveries.all()]})
  count=order_qs.count()
  return Response({'businesses':businesses,'selected_business':{'id':str(business.pk),'name':business.name,'district':business.district,'verification_status':business.verification_status,'review_notes':business.review_notes,'tax_registration':business.tax_registration},'period_days':days,'summary':{'orders':count,'gross_sales':float(gross),'delivered_sales':float(delivered),'units_sold':units,'average_order_value':float(gross/count) if count else 0},'statuses':statuses,'daily_sales':[{'date':row['day'].isoformat(),'orders':row['orders'],'units':row['units'],'gross_sales':float(row['gross_sales'])} for row in daily],'top_products':[{'name':row['product_name'],'units':row['units'],'gross_sales':float(row['gross_sales'])} for row in top],'orders':order_rows})
class BusinessViewSet(viewsets.ReadOnlyModelViewSet):
 queryset=Business.objects.filter(active=True).filter(Q(verification_status=Business.Verification.VERIFIED)|Q(is_demo=True)).select_related('category'); serializer_class=BusinessSerializer; permission_classes=[AllowAny]; lookup_field='slug'; filter_backends=[filters.SearchFilter]; search_fields=['name','description','district','sector','category__name']
 def get_queryset(self):
  qs=super().get_queryset(); district=self.request.query_params.get('district'); category=self.request.query_params.get('category'); verified=self.request.query_params.get('verified')
  if district: qs=qs.filter(district__icontains=district)
  if category: qs=qs.filter(category__name__iexact=category)
  if verified=='true': qs=qs.filter(verification_status='verified')
  return qs
 @action(detail=False,methods=['post'],permission_classes=[IsAuthenticated],parser_classes=[MultiPartParser,FormParser],url_path='register')
 def register_business(self,request):
  data=request.data
  required=['name','category','district','phone','email','address','tax_registration']
  missing=[key for key in required if not str(data.get(key,'')).strip()]
  if missing: return Response({'detail':'Complete all required business details: '+', '.join(missing)+'.'},status=400)
  category=Category.objects.filter(pk=data.get('category')).first()
  if not category: return Response({'detail':'Choose a valid business category.'},status=400)
  tax_registration=data.get('tax_registration')
  if tax_registration not in [Business.TaxRegistration.NOT_REGISTERED,Business.TaxRegistration.VAT_REGISTERED]:
   return Response({'detail':'Select whether this business is VAT registered.'},status=400)
  vat_tin=data.get('vat_tin','').strip()
  if tax_registration==Business.TaxRegistration.VAT_REGISTERED and not vat_tin:
   return Response({'detail':'A VAT registered business must provide its TIN.'},status=400)
  uploads={'rdb_registration':request.FILES.get('rdb_registration'),'tin_certificate':request.FILES.get('tin_certificate'),'owner_id':request.FILES.get('owner_id'),'vat_certificate':request.FILES.get('vat_certificate'),'ebm_approval':request.FILES.get('ebm_approval'),'ebm_commitment':request.FILES.get('ebm_commitment')}
  if not uploads['rdb_registration'] and not uploads['tin_certificate']:
   return Response({'detail':'Upload either the RDB registration certificate or TIN certificate.'},status=400)
  if not uploads['owner_id']: return Response({'detail':'Upload the owner’s ID or passport.'},status=400)
  if tax_registration==Business.TaxRegistration.VAT_REGISTERED and not uploads['vat_certificate']:
   return Response({'detail':'VAT registered businesses must upload their VAT certificate.'},status=400)
  for field,uploaded in uploads.items():
   if uploaded:
    signature=uploaded.read(1024); uploaded.seek(0); ext=Path(uploaded.name).suffix.lower()
    matches=(ext=='.pdf' and b'%PDF-' in signature) or (ext in ['.jpg','.jpeg'] and signature.startswith(b'\xff\xd8\xff')) or (ext=='.png' and signature.startswith(b'\x89PNG\r\n\x1a\n'))
    if uploaded.size>40*1024*1024:
     return Response({'detail':f'{field}: files can be up to 40 MB. This file is {uploaded.size//(1024*1024)} MB.'},status=400)
    if not matches:
     return Response({'detail':f'{field}: the file contents do not match a PDF, JPG, or PNG. Please choose a valid document in one of those formats.'},status=400)
  try:
   with transaction.atomic():
    business=Business.objects.create(owner=request.user,name=data['name'].strip()[:180],slug=f"{slugify(data['name'])[:40] or 'business'}-{secrets.token_hex(3)}",description=data.get('description','').strip(),category=category,district=data['district'].strip()[:100],sector=data.get('sector','').strip()[:100],phone=data['phone'].strip()[:30],email=data['email'].strip()[:254],address=data['address'].strip()[:240],tax_registration=tax_registration,vat_tin=vat_tin[:20],prices_include_vat=str(data.get('prices_include_vat','true')).lower()=='true',verification_status=Business.Verification.PENDING,active=False)
    for field,uploaded in uploads.items():
     if uploaded:
      BusinessVerification.objects.create(business=business,document_type=field,document=uploaded)
  except (ValueError,TypeError):
   return Response({'detail':'Review the business details and try again.'},status=400)
  return Response({'id':str(business.pk),'name':business.name,'verification_status':business.verification_status,'detail':'Application submitted for administrator review.'},status=201)
class CategoryViewSet(viewsets.ReadOnlyModelViewSet): queryset=Category.objects.all(); serializer_class=CategorySerializer; permission_classes=[AllowAny]; lookup_field='slug'
class ProductViewSet(viewsets.ModelViewSet):
 queryset=Product.objects.filter(active=True,business__active=True).filter(Q(business__verification_status=Business.Verification.VERIFIED)|Q(business__is_demo=True)).select_related('business','category'); serializer_class=ProductSerializer; filter_backends=[filters.SearchFilter]; search_fields=['name','description','business__name','business__district','category__name']
 def get_queryset(self):
  qs=super().get_queryset()
  if self.action in ['retrieve','update','partial_update','destroy'] and self.request.user.is_authenticated:
   owned=Business.objects.filter(Q(owner=self.request.user)|Q(members__user=self.request.user,members__active=True,members__role__in=['owner','manager'])).distinct()
   qs=(qs|Product.objects.filter(business__in=owned).select_related('business','category')).distinct()
  business=self.request.query_params.get('business'); available=self.request.query_params.get('available'); category=self.request.query_params.get('category')
  if business: qs=qs.filter(business_id=business)
  if available=='true': qs=qs.filter(stock__gt=0)
  if category: qs=qs.filter(category__name__iexact=category)
  return qs
 def get_permissions(self): return [AllowAny()] if self.action in ['list','retrieve'] else [IsAuthenticated()]
 @action(detail=False,methods=['get'],permission_classes=[IsAuthenticated],url_path='manage')
 def manage(self,request):
  business_id=request.query_params.get('business')
  owned=Business.objects.filter(Q(owner=request.user)|Q(members__user=request.user,members__active=True,members__role__in=['owner','manager'])).distinct()
  business=owned.filter(pk=business_id).first() if business_id else owned.first()
  if business is None: return Response({'detail':'Choose a business you own or manage.'},status=404)
  products=Product.objects.filter(business=business).select_related('business','category').order_by('-created_at')
  return Response({'business':{'id':str(business.pk),'name':business.name,'verification_status':business.verification_status},'products':ProductSerializer(products,many=True).data})
 def perform_create(self,serializer):
  business=Business.objects.filter(Q(owner=self.request.user)|Q(members__user=self.request.user,members__active=True,members__role__in=['owner','manager'])).filter(pk=self.request.data.get('business')).first()
  if business is None: raise PermissionDenied('You must own or manage this business to add products.')
  serializer.save(business=business)
 def perform_update(self,serializer):
  p=self.get_object()
  if not (p.business.owner_id==self.request.user.id or p.business.members.filter(user=self.request.user,active=True,role__in=['owner','manager']).exists()): raise PermissionDenied('Business ownership or manager access is required.')
  serializer.save(business=p.business)
 def perform_destroy(self,instance):
  if not (instance.business.owner_id==self.request.user.id or instance.business.members.filter(user=self.request.user,active=True,role__in=['owner','manager']).exists()): raise PermissionDenied('Business ownership or manager access is required.')
  instance.delete()
class OrderViewSet(viewsets.ModelViewSet):
 serializer_class=OrderSerializer
 http_method_names=['get','post','head','options']
 def get_permissions(self):
  if self.action in ['create','track','list']: return [AllowAny()]
  return [IsAuthenticated()]
 def get_queryset(self):
  if self.request.user.is_staff: return Order.objects.prefetch_related('items').all()
  if self.request.user.is_authenticated: return Order.objects.filter(customer=self.request.user).prefetch_related('items')
  return Order.objects.none()
 @action(detail=False,methods=['get'],permission_classes=[AllowAny],url_path='track')
 def track(self,request):
  reference=request.query_params.get('reference','').strip(); phone=request.query_params.get('phone','').strip()
  if not reference or not phone: return Response({'detail':'Order reference and checkout phone are required.'},status=400)
  order=Order.objects.filter(reference__iexact=reference,guest_phone=phone).prefetch_related('items').first()
  if not order: return Response({'detail':'No order matches those details.'},status=404)
  return Response(OrderSerializer(order).data)
 def create(self,request,*args,**kwargs):
  items=request.data.get('items',[])
  if not items or len(items)>40: return Response({'detail':'Add between 1 and 40 products.'},status=400)
  payment_method=request.data.get('payment_method','cash')
  if payment_method not in ['cash','cash_on_delivery','mtn_momo','airtel_money']: return Response({'detail':'Unsupported payment method.'},status=400)
  try:
   with transaction.atomic():
    product_ids=[x['product_id'] for x in items]
    products={str(p.pk):p for p in Product.objects.select_for_update().filter(pk__in=product_ids,active=True,business__active=True).filter(Q(business__verification_status=Business.Verification.VERIFIED)|Q(business__is_demo=True))}
    subtotal=Decimal('0.00'); tax_total=Decimal('0.00'); extra_tax=Decimal('0.00'); lines=[]
    for row in items:
     p=products.get(str(row['product_id'])); qty=int(row['quantity'])
     if p is None or qty<1 or qty>50: return Response({'detail':'An item or quantity is invalid.'},status=400)
     if p.stock<qty: return Response({'detail':f'Not enough stock for {p.name}.'},status=409)
     line_total=p.price*qty; vat_rate=Decimal('18.00') if p.business.tax_registration==Business.TaxRegistration.VAT_REGISTERED and p.vat_category==Product.VATCategory.STANDARD else Decimal('0.00')
     vat_amount=(line_total*vat_rate/(Decimal('100.00')+vat_rate) if p.business.prices_include_vat else line_total*vat_rate/Decimal('100.00')).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP) if vat_rate else Decimal('0.00')
     subtotal+=line_total; tax_total+=vat_amount
     if vat_rate and not p.business.prices_include_vat: extra_tax+=vat_amount
     lines.append((p,qty,line_total,vat_rate,vat_amount,p.business.prices_include_vat))
    total=subtotal+extra_tax
    order=Order.objects.create(reference='IM-'+secrets.token_hex(4).upper(),customer=request.user if request.user.is_authenticated else None,guest_name=request.data.get('guest_name','Guest shopper')[:120],guest_email=(request.data.get('guest_email') or (request.user.email if request.user.is_authenticated else ''))[:254],guest_phone=request.data.get('guest_phone','')[:30],payment_method=request.data.get('payment_method','cash'),subtotal=subtotal,tax_total=tax_total,total=total,delivery_address=request.data.get('delivery_address','')[:300])
    for p,qty,line_total,vat_rate,vat_amount,vat_included in lines:
     Product.objects.filter(pk=p.pk).update(stock=F('stock')-qty); OrderItem.objects.create(order=order,product=p,business=p.business,product_name=p.name,unit_price=p.price,price_per_kg=p.price_per_kg,quantity=qty,line_total=line_total,vat_category=p.vat_category,vat_rate=vat_rate,vat_amount=vat_amount,vat_included=vat_included); InventoryMovement.objects.create(product=p,quantity_change=-qty,reason=f'Order {order.reference}')
    if order.payment_method not in ['cash','cash_on_delivery','mtn_momo','airtel_money']: return Response({'detail':'Unsupported payment method.'},status=400)
    if order.payment_method in ['mtn_momo','airtel_money']:
     # Credential-free architecture: pending payment is never marked paid by customer input.
     Payment.objects.create(order=order,provider=order.payment_method,amount=order.total,idempotency_key=secrets.token_urlsafe(24))
    transaction.on_commit(lambda order_id=order.pk: send_order_receipt(order_id))
    return Response(OrderSerializer(order).data,status=201)
  except (ValueError,KeyError,TypeError): return Response({'detail':'Invalid order information.'},status=400)
 @action(detail=True,methods=['post'],permission_classes=[IsAuthenticated])
 def cancel(self,request,pk=None):
  order=self.get_object()
  if order.customer_id!=request.user.id or order.status!='pending': return Response({'detail':'This order cannot be cancelled.'},status=403)
  with transaction.atomic():
   for item in order.items.select_related('product'):
    Product.objects.filter(pk=item.product_id).update(stock=F('stock')+item.quantity); InventoryMovement.objects.create(product=item.product,quantity_change=item.quantity,reason=f'Cancel {order.reference}')
   order.status='cancelled'; order.save(update_fields=['status'])
  return Response(OrderSerializer(order).data)
class BookingViewSet(viewsets.ModelViewSet):
 serializer_class=BookingSerializer; http_method_names=['get','post','head','options']
 def get_permissions(self): return [AllowAny()] if self.action in ['create','track'] else [IsAuthenticated()]
 def get_queryset(self): return Booking.objects.filter(customer=self.request.user).select_related('service','service__business') if self.request.user.is_authenticated else Booking.objects.none()
 @action(detail=False,methods=['get'],permission_classes=[AllowAny],url_path='track')
 def track(self,request):
  reference=request.query_params.get('reference','').strip(); phone=request.query_params.get('phone','').strip()
  if not reference or not phone: return Response({'detail':'Booking reference and booking phone are required.'},status=400)
  booking=Booking.objects.filter(reference__iexact=reference,guest_phone=phone).select_related('service','service__business').first()
  if not booking: return Response({'detail':'No booking matches those details.'},status=404)
  return Response(BookingSerializer(booking).data)
 def create(self,request,*args,**kwargs):
  s=Service.objects.filter(pk=request.data.get('service'),active=True,business__active=True).filter(Q(business__verification_status=Business.Verification.VERIFIED)|Q(business__is_demo=True)).first()
  if not s: return Response({'detail':'Choose an available service.'},status=400)
  data=request.data.copy(); data['reference']='BK-'+secrets.token_hex(4).upper()
  serializer=self.get_serializer(data=data); serializer.is_valid(raise_exception=True)
  starts=serializer.validated_data['starts_at']; ends=serializer.validated_data['ends_at']; party=serializer.validated_data['party_size']
  if ends<=starts or party<1 or party>s.capacity: return Response({'detail':'Time or party size is not available.'},status=400)
  conflict=Booking.objects.filter(service=s,status__in=['pending','confirmed'],starts_at__lt=ends,ends_at__gt=starts).aggregate(total=Sum('party_size'))['total'] or 0
  if conflict+party>s.capacity: return Response({'detail':'That time is fully booked.'},status=409)
  subtotal=s.price*party; vat_rate=Decimal('18.00') if s.business.tax_registration==Business.TaxRegistration.VAT_REGISTERED and s.vat_category==Product.VATCategory.STANDARD else Decimal('0.00')
  vat_amount=(subtotal*vat_rate/(Decimal('100.00')+vat_rate) if s.business.prices_include_vat else subtotal*vat_rate/Decimal('100.00')).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP) if vat_rate else Decimal('0.00')
  total=subtotal if s.business.prices_include_vat or not vat_rate else subtotal+vat_amount
  serializer.save(reference=data['reference'],service=s,customer=request.user if request.user.is_authenticated else None,guest_name=request.data.get('guest_name','Guest')[:120],guest_phone=request.data.get('guest_phone','')[:30],unit_price=s.price,subtotal=subtotal,vat_category=s.vat_category,vat_rate=vat_rate,vat_amount=vat_amount,vat_included=s.business.prices_include_vat,total=total); return Response(serializer.data,status=201)
class ServiceViewSet(viewsets.ModelViewSet):
 queryset=Service.objects.filter(active=True,business__active=True).filter(Q(business__verification_status=Business.Verification.VERIFIED)|Q(business__is_demo=True)).select_related('business'); serializer_class=ServiceSerializer; permission_classes=[AllowAny]
 def get_queryset(self):
  qs=super().get_queryset()
  if self.action in ['retrieve','update','partial_update','destroy'] and self.request.user.is_authenticated:
   owned=Business.objects.filter(Q(owner=self.request.user)|Q(members__user=self.request.user,members__active=True,members__role__in=['owner','manager'])).distinct()
   qs=(qs|Service.objects.filter(business__in=owned).select_related('business')).distinct()
  business=self.request.query_params.get('business')
  return qs.filter(business_id=business) if business else qs
 def get_permissions(self): return [AllowAny()] if self.action in ['list','retrieve','availability'] else [IsAuthenticated()]
 @action(detail=False,methods=['get'],permission_classes=[IsAuthenticated],url_path='manage')
 def manage(self,request):
  business_id=request.query_params.get('business')
  owned=Business.objects.filter(Q(owner=request.user)|Q(members__user=request.user,members__active=True,members__role__in=['owner','manager'])).distinct()
  business=owned.filter(pk=business_id).first() if business_id else owned.first()
  if business is None: return Response({'detail':'Choose a business you own or manage.'},status=404)
  services=Service.objects.filter(business=business).select_related('business').order_by('name')
  return Response({'business':{'id':str(business.pk),'name':business.name,'verification_status':business.verification_status},'services':ServiceSerializer(services,many=True).data})
 def perform_create(self,serializer):
  business=Business.objects.filter(Q(owner=self.request.user)|Q(members__user=self.request.user,members__active=True,members__role__in=['owner','manager'])).filter(pk=self.request.data.get('business')).first()
  if business is None: raise PermissionDenied('You must own or manage this business to register a service.')
  serializer.save(business=business)
 def perform_update(self,serializer):
  service=self.get_object()
  if not (service.business.owner_id==self.request.user.id or service.business.members.filter(user=self.request.user,active=True,role__in=['owner','manager']).exists()): raise PermissionDenied('Business ownership or manager access is required.')
  serializer.save(business=service.business)
 def perform_destroy(self,instance):
  if not (instance.business.owner_id==self.request.user.id or instance.business.members.filter(user=self.request.user,active=True,role__in=['owner','manager']).exists()): raise PermissionDenied('Business ownership or manager access is required.')
  instance.delete()
 @action(detail=True,methods=['get'],permission_classes=[AllowAny])
 def availability(self,request,pk=None):
  service=self.get_object()
  try:
   starts=timezone.datetime.fromisoformat(request.query_params.get('starts_at','')); ends=timezone.datetime.fromisoformat(request.query_params.get('ends_at','')); party=max(1,int(request.query_params.get('party_size',1)))
  except (ValueError,TypeError): return Response({'available':False,'remaining':0,'detail':'Choose a valid date, time, and party size.'},status=400)
  if timezone.is_naive(starts) or timezone.is_naive(ends) or ends<=starts or party>service.capacity:
   return Response({'available':False,'remaining':0,'detail':'Choose a valid date, time, and party size.'},status=400)
  booked=Booking.objects.filter(service=service,status__in=['pending','confirmed'],starts_at__lt=ends,ends_at__gt=starts).aggregate(total=Sum('party_size'))['total'] or 0
  remaining=max(0,service.capacity-booked)
  return Response({'available':remaining>=party,'remaining':remaining,'capacity':service.capacity,'starts_at':starts,'ends_at':ends})
class ReviewViewSet(viewsets.ModelViewSet):
 serializer_class=ReviewSerializer; http_method_names=['get','post','head','options']
 def get_permissions(self): return [AllowAny()] if self.action=='list' else [IsAuthenticated()]
 def get_queryset(self):
  qs=Review.objects.filter(approved=True).select_related('customer')
  business=self.request.query_params.get('business')
  return qs.filter(business_id=business) if business else qs.none()
 def create(self,request,*args,**kwargs):
  try: business=Business.objects.get(pk=request.data.get('business'),active=True); order=Order.objects.get(pk=request.data.get('order'),customer=request.user,status='delivered')
  except (Business.DoesNotExist,Order.DoesNotExist,ValidationError,ValueError,TypeError): return Response({'detail':'A review requires your completed order and its business.'},status=400)
  if not order.items.filter(business=business).exists(): return Response({'detail':'That order does not include this business.'},status=400)
  if Review.objects.filter(order=order,business=business).exists(): return Response({'detail':'You already reviewed this purchase.'},status=409)
  serializer=self.get_serializer(data=request.data)
  serializer.is_valid(raise_exception=True)
  serializer.save(business=business,order=order,customer=request.user,approved=True)
  return Response(serializer.data,status=201)
class PaymentWebhookView(APIView):
 permission_classes=[IsAdminUser]
 def post(self,request):
  # Production adapters must verify the provider signature before calling this state transition.
  return Response({'detail':'Configure a provider adapter and signature verification before enabling payment webhooks.'},status=501)

class AddressViewSet(viewsets.ModelViewSet):
 serializer_class=AddressSerializer
 permission_classes=[IsAuthenticated]
 def get_queryset(self): return Address.objects.filter(user=self.request.user).order_by('-is_default','-id')
 def perform_create(self,serializer):
  if serializer.validated_data.get('is_default'): Address.objects.filter(user=self.request.user,is_default=True).update(is_default=False)
  serializer.save(user=self.request.user)
 def perform_update(self,serializer):
  if serializer.validated_data.get('is_default'): Address.objects.filter(user=self.request.user,is_default=True).exclude(pk=serializer.instance.pk).update(is_default=False)
  serializer.save()

class FavoriteViewSet(viewsets.ModelViewSet):
 serializer_class=FavoriteSerializer
 permission_classes=[IsAuthenticated]
 http_method_names=['get','post','delete','head','options']
 def get_queryset(self): return Favorite.objects.filter(user=self.request.user).select_related('business','product')
 def perform_create(self,serializer):
  serializer.save(user=self.request.user)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
 serializer_class=NotificationSerializer
 permission_classes=[IsAuthenticated]
 def get_queryset(self): return Notification.objects.filter(user=self.request.user).order_by('-created_at')
 @action(detail=True,methods=['post'])
 def read(self,request,pk=None):
  notification=self.get_object()
  if notification.read_at is None:
   notification.read_at=timezone.now()
   notification.save(update_fields=['read_at'])
  return Response(NotificationSerializer(notification).data)
 @action(detail=False,methods=['post'])
 def read_all(self,request):
  updated=self.get_queryset().filter(read_at__isnull=True).update(read_at=timezone.now())
  return Response({'updated':updated})

class ConversationViewSet(viewsets.ModelViewSet):
 serializer_class=ConversationSerializer
 permission_classes=[IsAuthenticated]
 http_method_names=['get','post','head','options']
 def get_queryset(self):
  owned=Business.objects.filter(Q(owner=self.request.user)|Q(members__user=self.request.user,members__active=True,members__role__in=['owner','manager','staff']))
  return Conversation.objects.filter(Q(customer=self.request.user)|Q(business__in=owned)).distinct().select_related('business','customer').prefetch_related('messages__sender').order_by('-created_at')
 def perform_create(self,serializer):
  serializer.save(customer=self.request.user)
 def create(self,request,*args,**kwargs):
  business_id=request.data.get('business')
  business=Business.objects.filter(pk=business_id,active=True).first()
  if not business: return Response({'detail':'Choose an available business.'},status=400)
  conversation,_=Conversation.objects.get_or_create(business=business,customer=request.user)
  body=str(request.data.get('message','')).strip()
  if body: Message.objects.create(conversation=conversation,sender=request.user,body=body[:5000])
  return Response(ConversationSerializer(conversation).data,status=201)
 @action(detail=True,methods=['post'])
 def send(self,request,pk=None):
  conversation=self.get_object()
  body=str(request.data.get('body','')).strip()
  if not body or len(body)>5000: return Response({'detail':'Message content must be between 1 and 5000 characters.'},status=400)
  message=Message.objects.create(conversation=conversation,sender=request.user,body=body)
  return Response({'id':message.id,'sender':message.sender.username,'body':message.body,'created_at':message.created_at},status=201)

class ComplaintViewSet(viewsets.ModelViewSet):
 serializer_class=ComplaintSerializer
 permission_classes=[IsAuthenticated]
 http_method_names=['get','post','head','options']
 def get_queryset(self):
  owned=Business.objects.filter(Q(owner=self.request.user)|Q(members__user=self.request.user,members__active=True,members__role__in=['owner','manager']))
  if self.request.user.is_staff: return Complaint.objects.all().select_related('business','reporter')
  return Complaint.objects.filter(Q(reporter=self.request.user)|Q(business__in=owned)).distinct().select_related('business','reporter').order_by('-created_at')
 def perform_create(self,serializer): serializer.save(reporter=self.request.user)
