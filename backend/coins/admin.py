'''Contains all database models for the coins django app'''
from django.contrib import admin
from backend.coins.models import Coin

admin.site.register(Coin)
