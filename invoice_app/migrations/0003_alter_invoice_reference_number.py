# Generated by Django 4.2.7 on 2024-12-08 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice_app', '0002_invoice_is_quotation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='reference_number',
            field=models.CharField(editable=False, max_length=14),
        ),
    ]
