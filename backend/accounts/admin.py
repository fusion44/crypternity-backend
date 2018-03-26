from django.contrib import admin
from backend.accounts.models import Address, Peer, Account

admin.site.register(Address)
admin.site.register(Peer)
admin.site.register(Account)
