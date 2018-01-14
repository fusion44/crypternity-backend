import json
import graphene

from graphene_django.types import DjangoObjectType

from backend.accounts.models import Account


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
        return Account.objects.all()


class CreateAccountMutation(graphene.relay.ClientIDMutation):
    class Input:
        name = graphene.String()
        description = graphene.String()

    status = graphene.Int()
    formErrors = graphene.String()
    account = graphene.Field(AccountType)

    @classmethod
    def mutate(cls, root, info, input: Input):
        if not info.user.is_authenticated:
            return CreateAccountMutation(status=403)
        name = input.get("name", "").strip()
        description = input.get("description", "").strip()

        # TODO: validate input using django forms or whatnot
        if not name or not description:
            return CreateAccountMutation(
                status=400,
                formErrors=json.dumps({
                    "account": ["Please enter valid account data"]
                }))
        obj = Account.objects.create(creator=info.user, name=name)
        return CreateAccountMutation(status=200, account=obj)
