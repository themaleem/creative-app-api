# Generated by Django 2.2.5 on 2019-11-24 23:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('showcase', '0002_auto_20191125_0012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='showcase',
            name='title',
            field=models.CharField(max_length=50),
        ),
    ]
