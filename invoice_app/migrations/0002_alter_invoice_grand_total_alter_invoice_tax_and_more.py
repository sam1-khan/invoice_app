# Generated by Django 4.2.7 on 2024-11-19 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='grand_total',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=16),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='tax',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=16),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='total_price',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=16),
        ),
    ]
