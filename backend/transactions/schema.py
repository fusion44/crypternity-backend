import json
import graphene
import time

from django.db.models import QuerySet
from graphene_django.types import DjangoObjectType

from backend.transactions.models import Transaction


class TransactionType(DjangoObjectType):
    class Meta:
        model = Transaction


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
