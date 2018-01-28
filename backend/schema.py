import graphene

import backend.accounts.schema
import backend.transactions.schema
import backend.user_profile.schema


class Query(backend.user_profile.schema.Query, backend.accounts.schema.Query,
            backend.transactions.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


class Mutation(graphene.ObjectType):
    create_account = backend.accounts.schema.CreateAccountMutation.Field()
    account_refresh_transactions = backend.accounts.schema.AccountRefreshTransactionsMutation.Field(
    )


schema = graphene.Schema(query=Query, mutation=Mutation)