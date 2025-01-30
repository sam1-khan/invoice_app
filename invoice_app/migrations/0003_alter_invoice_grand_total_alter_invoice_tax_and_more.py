# Generated by Django 4.2.7 on 2025-01-30 17:11

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice_app', '0002_invoice_transit_charges'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='grand_total',
            field=models.DecimalField(decimal_places=3, default=0, editable=False, max_digits=16),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='tax',
            field=models.DecimalField(decimal_places=3, default=0, editable=False, max_digits=16),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='tax_percentage',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='total_price',
            field=models.DecimalField(decimal_places=3, default=0, editable=False, max_digits=16),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='transit_charges',
            field=models.DecimalField(blank=True, decimal_places=3, default=0, max_digits=16, null=True),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='quantity',
            field=models.DecimalField(decimal_places=3, max_digits=16, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='total_price',
            field=models.DecimalField(decimal_places=3, editable=False, max_digits=16),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='unit_price',
            field=models.DecimalField(decimal_places=3, max_digits=16, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
