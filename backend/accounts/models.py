from django.db import models


class Account(models.Model):
    SERVICE_TYPES = (('binance', 'Binance',
                      'api'), ('bitfinex', 'Bitfinex',
                               'api'), ('coinbase', 'Coinbase', 'api'),
                     ('cryptopia', 'Cryptopia', 'api'), ('kraken', 'Kraken',
                                                         'api'))

    id = models.AutoField(primary_key=True)

    owner = models.ForeignKey(
        'auth.user',
        on_delete=models.CASCADE,
    )

    name = models.CharField(max_length=50)

    slug = models.SlugField(max_length=50)

    service_type = models.CharField(max_length=50)

    api_key = models.CharField(max_length=100)

    api_secret = models.CharField(max_length=100)

    creation_date = models.DateTimeField(auto_now_add=True)

    symbols = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name
