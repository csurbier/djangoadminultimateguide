# Generated by Django 2.2.7 on 2019-11-19 14:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0003_auto_20191119_1415'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='author',
            name='picture',
        ),
    ]
