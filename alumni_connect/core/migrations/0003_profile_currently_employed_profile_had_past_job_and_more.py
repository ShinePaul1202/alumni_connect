# Generated by Django 5.2.4 on 2025-07-16 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_profile_company_name_profile_job_title_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='currently_employed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profile',
            name='had_past_job',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profile',
            name='past_company_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='past_job_title',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
