import json
import graphene
import time

from django.db.models import QuerySet
from graphene_django.types import DjangoObjectType

from backend.transactions.models import Transaction
from backend.transactions.importers.livecoin import import_data_livecoin


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


class TransactionData(graphene.InputObjectType):
    """Data to import from the client. This should normally be already pre-processed data.
    """
    date = graphene.String()
    transaction_type = graphene.String(
        required=True,
        description="""
Options:

exchange - exchange between currencies on this peer
transfer - transfer one coin from one wallet to another
buy - buy cryptos from fiat
sell - sell cryptos for fiat
income - receive cryptos for a service or selling of a good (refferal bonus, selling of hardware etc)
expense - pay for a service or a good (online subscription, buy of an hardware)
mining - mining income
""")
    transaction_type_raw = graphene.String(
        description=
        """The raw unprocessed transaction type coming from the data source.
        Can be different from peer to peer. This is included so the importer in the server might implement this in a non standard way"""
    )
    spent_currency = graphene.String(required=True)
    spent_amount = graphene.Float(required=True)
    source_peer = graphene.ID()
    acquired_currency = graphene.String()
    acquired_amount = graphene.Float()
    target_peer = graphene.ID()
    fee_currency = graphene.String()
    fee_amount = graphene.Float()
    tags = graphene.List(graphene.String)


class ImportTransactionInput(graphene.InputObjectType):
    """The input type for the import mutation.
    """
    service_type = graphene.String()
    import_mechanism = graphene.String(
        required=True,
        description="""
                The mechanism of import: \n
                * csv - Import via file (csv, excel, etc)
                * manual - Import with manually entered input
                """)
    transactions = graphene.List(TransactionData, required=True)


class ImportTransactionsMutation(graphene.relay.ClientIDMutation):
    """Contains the import mutations"""

    class Input:
        """The input class for the mutation"""
        data = graphene.Field(ImportTransactionInput, required=True)

    status = graphene.Int()
    formErrors = graphene.String()
    transactions = graphene.List(TransactionType)

    @classmethod
    def mutate(cls, root, info, input=None):
        if not info.context.user.is_authenticated:
            return ImportTransactionsMutation(status=403)

        if input.data.service_type == "livecoin":
            transactions = import_data_livecoin(input.data, info.context.user)
            return ImportTransactionsMutation(
                status=200, transactions=transactions)

        return ImportTransactionsMutation(
            status=404,
            formErrors="Service type {} not found".format(
                input.data.service_type))
