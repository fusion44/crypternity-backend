# Generated by Django 2.0.1 on 2018-01-28 13:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20180126_1320'),
    ]

    operations = [
        migrations.RenameField(
            model_name='account',
            old_name='creator',
            new_name='owner',
        ),
    ]
