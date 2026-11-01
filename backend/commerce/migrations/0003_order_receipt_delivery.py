from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('commerce', '0002_order_guest_email')]

    operations = [
        migrations.CreateModel(
            name='OrderReceiptDelivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('email', 'Email'), ('sms', 'Sms')], max_length=8)),
                ('recipient', models.CharField(blank=True, max_length=254)),
                ('status', models.CharField(choices=[('sent', 'Sent'), ('preview', 'Preview'), ('failed', 'Failed'), ('not_configured', 'Not configured')], max_length=20)),
                ('provider_reference', models.CharField(blank=True, max_length=120)),
                ('error_message', models.CharField(blank=True, max_length=300)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipt_deliveries', to='commerce.order')),
            ],
            options={'ordering': ['created_at']},
        ),
        migrations.AddIndex(
            model_name='orderreceiptdelivery',
            index=models.Index(fields=['order', 'channel'], name='commerce_or_order__9ea8b1_idx'),
        ),
    ]
