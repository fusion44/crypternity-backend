from django.db import models


class Account(models.Model):
    SERVICE_TYPES = (('binance', 'Binance'), ('bitfinex', 'Bitfinex'),
                     ('coinbase', 'Coinbase'), ('kraken', 'Kraken'))

    id = models.AutoField(primary_key=True)

    creator = models.ForeignKey(
        'auth.user',
        on_delete=models.CASCADE,
    )

    name = models.CharField(max_length=100)

    service_type = models.CharField(
        max_length=50,
        choices=SERVICE_TYPES,
    )

    api_key = models.CharField(max_length=100)

    api_secret = models.CharField(max_length=100)

    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
