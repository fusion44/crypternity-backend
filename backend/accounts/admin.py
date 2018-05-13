from django.contrib import admin
from backend.accounts.models import CryptoAddress, Peer, Account

admin.site.register(CryptoAddress)
admin.site.register(Peer)
admin.site.register(Account)
