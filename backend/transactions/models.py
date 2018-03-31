"""Contains all models necessary for the Transactions application"""

from django.db import models


class Transaction(models.Model):
    class Meta:
        ordering = ('-date', )

    """Database model for a single transaction"""
    id = models.AutoField(primary_key=True)

    owner = models.ForeignKey(
        related_name='owner',
        to='auth.user',
        on_delete=models.PROTECT,
    )

    date = models.DateTimeField()

    # Spent
    spent_currency = models.CharField(max_length=10)
    spent_amount = models.DecimalField(max_digits=19, decimal_places=10)
    source_peer = models.ForeignKey(
        default=1,
        related_name='source_peer',
        to='accounts.Peer',
        on_delete=models.PROTECT)

    # Acquired
    acquired_currency = models.CharField(max_length=10)
    acquired_amount = models.DecimalField(max_digits=19, decimal_places=10)
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
