from django.db import models


class Transaction(models.Model):

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
    source_account = models.ForeignKey(
        related_name='source_account',
        to='accounts.Account',
        on_delete=models.PROTECT)

    # Aquired
    aquired_currency = models.CharField(max_length=10)
    aquired_amount = models.DecimalField(max_digits=19, decimal_places=10)
    target_account = models.ForeignKey(
        related_name='target_account',
        to='accounts.Account',
        on_delete=models.PROTECT)

    # Fees and book prices are calculated using the mean price of the coin at that day
    fee_currency = models.CharField(max_length=10)
    fee_amount = models.DecimalField(max_digits=19, decimal_places=10)

    # book price is the price of the spent amount in BTC and FIAT
    book_price_eur = models.DecimalField(max_digits=19, decimal_places=10)
    book_price_btc = models.DecimalField(max_digits=19, decimal_places=10)

    # fee price is the price of the spent amount in BTC and FIAT
    book_price_fee_eur = models.DecimalField(max_digits=19, decimal_places=10)
    book_price_fee_btc = models.DecimalField(max_digits=19, decimal_places=10)

    def __str__(self):
        # convertion to float removes trailing 0's
        return "{} {} => {} {} ==> {} EUR".format(
            float(self.spent_amount), self.spent_currency,
            float(self.aquired_amount), self.aquired_currency,
            float(self.book_price_eur))
