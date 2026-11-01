from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from commerce.models import Category,Business,Product,Service

class Command(BaseCommand):
 help='Create clearly labeled demonstration listings; no real customer accounts or sales.'
 def handle(self,*args,**options):
  user,created=get_user_model().objects.get_or_create(username='demo-maker',defaults={'email':'demo@example.invalid','first_name':'Demo Maker'})
  if created: user.set_password('demo-only-change-me')
  user.is_staff=True
  user.is_superuser=True
  user.save()
  for name,icon in [('Fashion','◈'),('Food & drink','☕'),('Home & living','⌂'),('Experiences','⌁'),('Stay & travel','⌂')]: Category.objects.get_or_create(slug=slugify(name),defaults={'name':name,'icon':icon})
  entries=[('Imigongo Studio','Home & living','Handwoven sisal market basket','28500','photo-1590736969955-71cc94901144'),('Huye Mountain Coffee','Food & drink','Single origin Bourbon coffee','18500','photo-1559525839-b184a4d698c7'),('Moshions Kigali','Fashion','Umushanana — modern classic','95000','photo-1539109136881-3be0616acf4b'),('Amahoro Tours','Experiences','Volcanoes & golden monkeys','185000','photo-1516026672322-bc52d61a55d5')]
  for index,(bname,cat,pname,price,image) in enumerate(entries):
   category=Category.objects.get(name=cat); business,_=Business.objects.get_or_create(slug=slugify(bname),defaults={'owner':user,'name':bname,'category':category,'district':['Kicukiro','Huye','Nyarugenge','Musanze'][index],'phone':'+250000000000','description':'Demonstration listing for local preview. Business verification is pending.','verification_status':'pending','is_demo':True}); Product.objects.get_or_create(business=business,name=pname,defaults={'category':category,'description':'Clearly labeled demo listing. Confirm details with the seller.','price':price,'stock':10,'image_url':f'https://images.unsplash.com/{image}?auto=format&fit=crop&w=950&q=85'})
  bookables=[('Amahoro Tours','Experiences','Musanze','Volcanoes guided trek','A demonstration guided trek. Contact the business to confirm the route and conditions.',185000,12),('Virunga Eco Lodge','Stay & travel','Musanze','Lodge room reservation','Demonstration room inventory; the business confirms room type and final rate.',95000,8),('Kigali Soul Kitchen','Food & drink','Kigali','Restaurant table reservation','Demonstration table booking; the business confirms the seating time.',0,24)]
  for bname,cat,district,sname,description,price,capacity in bookables:
   category=Category.objects.get(name=cat); business,_=Business.objects.get_or_create(slug=slugify(bname),defaults={'owner':user,'name':bname,'category':category,'district':district,'phone':'+250000000000','description':'Demonstration listing for local preview. Business verification is pending.','verification_status':'pending','is_demo':True}); Service.objects.get_or_create(business=business,name=sname,defaults={'description':description,'price':price,'capacity':capacity})
  self.stdout.write(self.style.SUCCESS('Demo listings are ready. These are not verified businesses or genuine sales.'))
