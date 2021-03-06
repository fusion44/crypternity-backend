# Generated by Django 2.0.2 on 2018-03-15 19:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateTimeField()),
                ('spent_currency', models.CharField(max_length=10)),
                ('spent_amount', models.DecimalField(decimal_places=10, max_digits=19)),
                ('acquired_currency', models.CharField(max_length=10)),
                ('acquired_amount', models.DecimalField(decimal_places=10, max_digits=19)),
                ('fee_currency', models.CharField(max_length=10)),
                ('fee_amount', models.DecimalField(decimal_places=10, max_digits=19)),
                ('book_price_eur', models.DecimalField(decimal_places=10, max_digits=19)),
                ('book_price_btc', models.DecimalField(decimal_places=10, max_digits=19)),
                ('book_price_fee_eur', models.DecimalField(decimal_places=10, max_digits=19)),
                ('book_price_fee_btc', models.DecimalField(decimal_places=10, max_digits=19)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='owner', to=settings.AUTH_USER_MODEL)),
                ('source_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='source_account', to='accounts.Account')),
                ('target_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='target_account', to='accounts.Account')),
            ],
        ),
        migrations.CreateModel(
            name='TransactionUpdateHistoryEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateTimeField()),
                ('fetched_transactions', models.IntegerField()),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounts.Account')),
            ],
        ),
    ]
