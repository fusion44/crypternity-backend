import json
import graphene
import ccxt
import celery
from django.db.models import ObjectDoesNotExist

from graphene_django.types import DjangoObjectType

from backend.accounts.models import Peer, Account

from backend.accounts.tasks import async_update_account_trx

from backend.transactions.fetchers.coinbase import update_coinbase_trx


class PeerType(DjangoObjectType):
    class Meta:
        model = Peer


class SupportedService(graphene.ObjectType):
    short_name = graphene.String()
    long_name = graphene.String()
    importer = graphene.String()


class SupportedSymbol(graphene.ObjectType):
    symbol = graphene.String()
    base = graphene.String()
    quote = graphene.String()


class AccountType(DjangoObjectType):
    class Meta:
        model = Account


class Query(object):
    # Single account by ID or name
    get_account = graphene.Field(
        AccountType,
        id=graphene.Int(required=False),
        name=graphene.String(required=False))

    def resolve_get_account(self, info, **kwargs):
        account_id = kwargs.get('id')
        account_name = kwargs.get('name')

        if account_id is not None:
            return Account.objects.get(pk=account_id)
        if account_name is not None:
            return Account.objects.get(name=account_name)

    # Get all accounts where user has access rights
    all_accounts = graphene.List(AccountType)

    def resolve_all_accounts(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            return Account.objects.none()
        filtered = Account.objects.filter(owner=info.context.user)
        return filtered

    supported_services = graphene.List(SupportedService)

    def resolve_supported_services(self, info, **kwargs):
        l = []
        for val in Account.SERVICE_TYPES:
            s = SupportedService()
            s.short_name = val[0]
            s.long_name = val[1]
            s.importer = val[2]
            l.append(s)
        return l

    supported_symbols = graphene.List(
        SupportedSymbol, service=graphene.String(required=True))

    def resolve_supported_symbols(self, info, **kwargs):
        l = []
        if not info.context.user.is_authenticated:
            return l

        service_id = kwargs.get('service')
        try:
            exchange = getattr(ccxt, service_id)()
            markets = exchange.load_markets()
            for m in markets:
                market = markets[m]
                if market:
                    s = SupportedSymbol()
                    s.symbol = market["symbol"]
                    s.base = market["base"]
                    s.quote = market["quote"]
                    l.append(s)
        except AttributeError:
            # coinbase will land here
            # it is not supported by ccxt and will receive special treatment
            pass

        return l


class CreateAccountMutation(graphene.relay.ClientIDMutation):
    class Input:
        name = graphene.String()
        service_type = graphene.String()
        symbols = graphene.String()
        api_key = graphene.String()
        api_secret = graphene.String()

    status = graphene.Int()
    formErrors = graphene.String()
    account = graphene.Field(AccountType)

    @classmethod
    def mutate(cls, root, info, input: Input):
        if not info.context.user.is_authenticated:
            return CreateAccountMutation(status=403)
        name = input.get("name", "").strip()
        service_type = input.get("service_type", "").strip()
        symbols = input.get("symbols", "").strip()
        api_key = input.get("api_key", "").strip()
        api_secret = input.get("api_secret", "").strip()

        # TODO: validate input using django forms or whatnot
        if not name or not service_type:
            return CreateAccountMutation(
                status=400,
                formErrors=json.dumps({
                    "account": ["Please enter valid account data"]
                }))

        if Account.objects.filter(name=name).exists():
            print("exists")
            return CreateAccountMutation(
                status=422,
                formErrors=json.dumps({
                    "account": ["A account with this name exists"]
                }))

        obj = Account.objects.create(
            owner=info.context.user,
            name=name,
            slug=name,
            service_type=service_type,
            symbols=symbols,
            api_key=api_key,
            api_secret=api_secret)

        return CreateAccountMutation(status=200, account=obj)


class EditAccountMutation(graphene.relay.ClientIDMutation):
    class Input:
        account_id = graphene.Int()
        name = graphene.String()
        api_key = graphene.String()
        api_secret = graphene.String()

    status = graphene.Int()
    formErrors = graphene.String()
    account = graphene.Field(AccountType)

    @classmethod
    def mutate(cls, root, info, input: Input):
        if not info.context.user.is_authenticated:
            return EditAccountMutation(status=403)

        account_id = input.get("account_id", -1)
        name = input.get("name", "").strip()
        api_key = input.get("api_key", "").strip()
        api_secret = input.get("api_secret", "").strip()

        # TODO: validate input using django forms or whatnot
        if account_id < 0 or not name or not api_key or not api_secret:
            return EditAccountMutation(
                status=400,
                formErrors=json.dumps({
                    "account": ["Please enter valid account data"]
                }))

        try:
            account: Account = Account.objects.get(pk=account_id)
        except ObjectDoesNotExist:
            return EditAccountMutation(
                status=422,
                formErrors=json.dumps({
                    "account": ["Account does not exists"]
                }))

        if account.owner != info.context.user:
            return EditAccountMutation(status=403)

        if not account:
            return EditAccountMutation(
                status=422,
                formErrors=json.dumps({
                    "account": ["This account does not exist"]
                }))

        account.name = name
        account.api_key = api_key
        account.api_secret = api_secret
        account.save()

        return EditAccountMutation(status=200, account=account)


class AccountRefreshTransactionsMutation(graphene.relay.ClientIDMutation):
    class Input:
        account_id = graphene.String()

    status = graphene.Int()
    formErrors = graphene.String()
    msg = graphene.String()

    @classmethod
    def mutate(cls, root, info, input) -> "AccountRefreshTransactionsMutation":
        if not info.context.user.is_authenticated:
            return AccountRefreshTransactionsMutation(status=403)

        if input.get("account_id", -1) == -1:
            return AccountRefreshTransactionsMutation(status=400)

        account_id = input.get("account_id", -1).strip()

        try:
            id_int = int(account_id)
            if id_int < 0:
                raise ValueError("Invalid input")
        except ValueError as err:
            return AccountRefreshTransactionsMutation(status=400)

        account: Account = Account.objects.get(pk=account_id)

        if account.owner != info.context.user:
            return AccountRefreshTransactionsMutation(status=403)

        tid = account_id + account.name
        # celery.result will only be available until after the task has run once
        if hasattr(celery, "result") and celery.result.AsyncResult(
                tid).status == "RUNNING":
            print("skipping task")
            return AccountRefreshTransactionsMutation(
                msg="Task is already running", status=202)
        else:
            try:
                print("starting task")
                async_update_account_trx.apply_async(
                    args=[account_id], task_id=tid)
            except async_update_account_trx.OperationalError as err:
                print("Sending task raised: %r", err)
                return AccountRefreshTransactionsMutation(status=500)

        return AccountRefreshTransactionsMutation(msg="Working", status=200)
