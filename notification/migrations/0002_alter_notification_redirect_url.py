# Generated by Django 4.1.7 on 2023-03-13 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='redirect_url',
            field=models.URLField(blank=True, help_text='The URL to redirect to when to clicked', max_length=500, null=True),
        ),
    ]
