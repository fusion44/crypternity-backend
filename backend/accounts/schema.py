import json
import graphene

from graphene_django.types import DjangoObjectType

from backend.accounts.models import Account


class SupportedService(graphene.ObjectType):
    short_name = graphene.String()
    long_name = graphene.String()


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
        filtered = Account.objects.filter(creator=info.context.user)
        return filtered

    supported_services = graphene.List(SupportedService)

    def resolve_supported_services(self, info, **kwargs):
        l = []
        for val in Account.SERVICE_TYPES:
            s = SupportedService()
            s.short_name = val[0]
            s.long_name = val[1]
            l.append(s)
        return l


class CreateAccountMutation(graphene.relay.ClientIDMutation):
    class Input:
        name = graphene.String()
        service_type = graphene.String()
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
        api_key = input.get("api_key", "").strip()
        api_secret = input.get("api_secret", "").strip()

        # TODO: validate input using django forms or whatnot
        if not name or not service_type or not api_key or not api_secret:
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
            creator=info.context.user,
            name=name,
            slug=name,
            service_type=service_type,
            api_key=api_key,
            api_secret=api_secret)

        return CreateAccountMutation(status=200, account=obj)
