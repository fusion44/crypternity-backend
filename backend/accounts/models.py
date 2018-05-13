from django.db import models

from backend.coins.models import Coin


class Peer(models.Model):
    """
    Database model for a peer. A peer is something that can
    send or receive value. Usually it has an address or
    multiple addresses associated with it.
    """
    id = models.AutoField(primary_key=True)

    owner = models.ForeignKey(
        to='auth.user',
        on_delete=models.PROTECT,
    )

    name = models.CharField(max_length=100)

    class_type = models.CharField(max_length=50, editable=False)

    def save(self,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None,
             class_type="Peer"):
        """Set class type"""
        self.class_type = class_type
        super(Peer, self).save(force_insert, force_update, using,
                               update_fields)

    def __str__(self):
        return "[{}] {}".format(self.class_type, self.name)


class CryptoAddress(models.Model):
    """A crypto address to identify value flows"""

    class Meta:
        ordering = ("id", )

    id = models.AutoField(primary_key=True)

    # The peers this address belongs to
    peer = models.ForeignKey(Peer, on_delete=models.PROTECT)

    coin = models.ForeignKey(Coin, on_delete=models.PROTECT)

    address = models.CharField(max_length=256)

    address_str = models.CharField(max_length=300, blank=True)

    watch = models.BooleanField(default=False)

    def save(self,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None):
        """Calculate the address string before save"""
        self.address_str = "{}:{}".format(self.coin.symbol, self.address)
        super(CryptoAddress, self).save(force_insert, force_update, using,
                                        update_fields)

    def __str__(self):
        return self.address_str


class Account(Peer):
    '''
    An Account represents an Exchange like Binance or Cryptopia.
    Transactions from accounts are usually fetched via an API.
    In some cases only csv file import might be available.

    To see which account supports which type of import see the
    SERVICE_TYPES tuple.
    '''
    SERVICE_TYPES = (('binance', 'Binance',
                      'api'), ('bitfinex', 'Bitfinex',
                               'api'), ('coinbase', 'Coinbase', 'api'),
                     ('cryptopia', 'Cryptopia',
                      'api'), ('ethereum_wallet', 'Ethereum Wallet',
                               'public_address_import'),
                     ('kraken', 'Kraken', 'api'), ('livecoin', 'Livecoin',
                                                   'manual'))

    slug = models.SlugField(max_length=50)

    service_type = models.CharField(max_length=50)

    api_key = models.CharField(max_length=100, blank=True, null=True)

    api_secret = models.CharField(max_length=100, blank=True, null=True)

    creation_date = models.DateTimeField(auto_now_add=True)

    symbols = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
    )

    def save(self,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None):
        '''
        Save is overridden to set properly call Peers save method with the
        class_type parameter
        '''
        super(Account, self).save(force_insert, force_update, using,
                                  update_fields, "Account")
