from django.db import migrations, models

class Migration(migrations.Migration):
 dependencies=[('commerce','0012_product_image_file_product_video_file')]
 operations=[
  migrations.AddField(model_name='payment',name='escrow_status',field=models.CharField(choices=[('none','None'),('pending','Pending'),('held','Held'),('released','Released'),('refunded','Refunded'),('disputed','Disputed')],default='none',max_length=12)),
  migrations.AddField(model_name='payment',name='confirmation_pin_hash',field=models.CharField(blank=True,max_length=128)),
  migrations.AddField(model_name='payment',name='confirmation_pin_expires_at',field=models.DateTimeField(blank=True,null=True)),
  migrations.AddField(model_name='payment',name='buyer_confirmed_at',field=models.DateTimeField(blank=True,null=True)),
  migrations.AddField(model_name='payment',name='held_at',field=models.DateTimeField(blank=True,null=True)),
  migrations.AddField(model_name='payment',name='released_at',field=models.DateTimeField(blank=True,null=True)),
 ]
