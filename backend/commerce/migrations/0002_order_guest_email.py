from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('commerce', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='order',
            name='guest_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
    ]
