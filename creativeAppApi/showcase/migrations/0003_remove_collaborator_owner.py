# Generated by Django 2.2.5 on 2020-01-21 15:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('showcase', '0002_collaborator'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collaborator',
            name='owner',
        ),
    ]