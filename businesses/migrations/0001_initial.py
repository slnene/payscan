# Generated by Django 5.0 on 2024-12-01 22:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('agents', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Business',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('qr_code', models.ImageField(blank=True, null=True, upload_to='static/img/qrcodes/')),
                ('Dynamic_qr_code', models.ImageField(blank=True, null=True, upload_to='static/img/qrcodes_PAYMENTS/')),
                ('public_transport', models.BooleanField(default=0)),
                ('corridor', models.CharField(blank=True, default='N/A', max_length=100, null=True)),
                ('number_plate', models.CharField(blank=True, default='N/A', max_length=100, null=True)),
                ('fcm_token', models.CharField(blank=True, default='n/a', max_length=255, null=True)),
                ('default_pin', models.DecimalField(decimal_places=0, max_digits=5, null=True)),
                ('priority', models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ('agent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='agents.agent')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.payscanuser')),
            ],
        ),
    ]
