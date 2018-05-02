"""Contains all models necessary for the Transactions application"""

from django.db import models

from taggit.managers import TaggableManager


class Transaction(models.Model):
    """Database model for a single transaction"""

    # exchange between currencies
    TRX_TAG_EXCHANGE = "exchange"
    TRX_ICON_EXCHANGE = "shuffle"
    # transfer one coin from one wallet to another
    TRX_TAG_TRANSFER = "transfer"
    TRX_ICON_TRANSFER = "send"
    # buy cryptos from fiat
    TRX_TAG_BUY = "buy"
    TRX_ICON_BUY = "subdirectory_arrow_right"
    # sell cryptos for fiat
    TRX_TAG_SELL = "sell"
    TRX_ICON_SELL = "subdirectory_arrow_left"
    # income for a service or sell of a good (refferal bonus, selling of hardware etc)
    TRX_TAG_INCOME = "income"
    TRX_ICON_INCOME = "arrow_forward"
    # expense for a service or buy of a good (online subscription, buy of an hardware)
    TRX_TAG_EXPENSE = "expense"
    TRX_ICON_EXPENSE = "arrow_backward"
    # mining income
    TRX_TAG_MINING = "mining"
    TRX_ICON_MINING = "gavel"

    # for transactions that need attention by the user
    TRX_TAG_WARNING = "warning"
    TRX_ICON_WARNING = "warning"

    class Meta:
        ordering = ('-date', )

    id = models.AutoField(primary_key=True)

    owner = models.ForeignKey(
        related_name='owner',
        to='auth.user',
        on_delete=models.PROTECT,
    )

    date = models.DateTimeField()

    # Spent
    spent_currency = models.CharField(max_length=10, default="---")
    spent_amount = models.DecimalField(
        max_digits=19, decimal_places=10, default=0)
    source_peer = models.ForeignKey(
        default=1,
        related_name='source_peer',
        to='accounts.Peer',
        on_delete=models.PROTECT)

    # Acquired
    acquired_currency = models.CharField(max_length=10, default="---")
    acquired_amount = models.DecimalField(
        max_digits=19, decimal_places=10, default=0)
    target_peer = models.ForeignKey(
        default=1,
        related_name='target_peer',
        to='accounts.Peer',
        on_delete=models.PROTECT)

    # Fees and book prices are calculated using the mean price of the coin at that day
    fee_currency = models.CharField(max_length=10, default="---")
    fee_amount = models.DecimalField(
        max_digits=19, default=0, decimal_places=10)

    # book price is the price of the spent amount in BTC and FIAT
    book_price_eur = models.DecimalField(max_digits=19, decimal_places=10)
    book_price_btc = models.DecimalField(max_digits=19, decimal_places=10)

    # fee price is the price of the spent amount in BTC and FIAT
    book_price_fee_eur = models.DecimalField(
        max_digits=19, default=0, decimal_places=10)
    book_price_fee_btc = models.DecimalField(
        max_digits=19, default=0, decimal_places=10)

    tags = TaggableManager()

    icon = models.CharField(default="help_outline", max_length=100)

    def __str__(self):
        # convertion to float removes trailing 0's
        return "{} {} => {} {} ==> {} EUR".format(
            float(self.spent_amount), self.spent_currency,
            float(self.acquired_amount), self.acquired_currency,
            float(self.book_price_eur))


class TransactionUpdateHistoryEntry(models.Model):
    id = models.AutoField(primary_key=True)

    date = models.DateTimeField()

    account = models.ForeignKey(
        to='accounts.Account',
        on_delete=models.PROTECT,
    )

    fetched_transactions = models.IntegerField()

    def __str__(self):
        return "{} {} {}".format(self.account.id, self.date,
                                 self.fetched_transactions)
