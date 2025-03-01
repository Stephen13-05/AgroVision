# Generated by Django 5.1.6 on 2025-03-01 10:20

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PredictionHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prediction_type', models.CharField(choices=[('disease', 'Disease'), ('pest', 'Pest')], max_length=10)),
                ('image_url', models.URLField()),
                ('label', models.CharField(max_length=100)),
                ('confidence', models.FloatField()),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('location', models.CharField(default='Chittoor', max_length=100)),
                ('temperature', models.FloatField(blank=True, null=True)),
                ('humidity', models.FloatField(blank=True, null=True)),
                ('soil_moisture', models.FloatField(blank=True, null=True)),
                ('soil_ph', models.FloatField(blank=True, null=True)),
                ('treatment_plan', models.JSONField()),
            ],
            options={
                'ordering': ['-date_created'],
            },
        ),
    ]
