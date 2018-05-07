'''Contains the models for this app'''
from django.db import models


class Coin(models.Model):
    '''Database model representing a coin'''

    class Meta:
        ordering = ("symbol", )

    id = models.AutoField(primary_key=True)
    cc_id = models.IntegerField(unique=True)
    img_url = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    symbol = models.CharField(max_length=10)
    coin_name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=200)

    def __str__(self):
        '''Assembles a string description for this object'''
        return "{} - {}".format(self.symbol, self.full_name)
