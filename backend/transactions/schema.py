import json
import graphene
import time

from django.db.models import QuerySet
from graphene_django.types import DjangoObjectType

from backend.transactions.models import Transaction


class TransactionType(DjangoObjectType):
    class Meta:
        model = Transaction
        only_fields = [
            'id',
            'owner',
            'date',
            'spent_currency',
            'spent_amount',
            'source_peer',
            'acquired_currency',
            'acquired_amount',
            "target_peer",
            "fee_currency",
            "fee_amount",
            "book_price_eur",
            "book_price_btc",
            "book_price_fee_eur",
            "book_price_fee_btc",
            "icon",
        ]

    tags = graphene.List(graphene.String)

    @staticmethod
    def resolve_tags(self: Transaction, context, **kwargs):
        """Resolve all tags associated with this object"""
        return self.tags.all().order_by("name")


class Query(object):
    # Single transaction by ID
    get_transaction = graphene.Field(
        TransactionType, id=graphene.Int(required=True))

    def resolve_get_transaction(self, info, **kwargs) -> Transaction:
        if not info.context.user.is_authenticated:
            return None

        transaction_id = kwargs.get('id')

        if transaction_id is not None:
            t = Transaction.objects.get(pk=transaction_id)
            if t.owner == info.context.user:
                return t
            return None

    # Get all transaction where user has access rights
    all_transactions = graphene.List(TransactionType)

    def resolve_all_transactions(self, info, **kwargs) -> QuerySet:
        if not info.context.user.is_authenticated:
            return Transaction.objects.none()
        filtered = Transaction.objects.filter(owner=info.context.user)
        return filtered
