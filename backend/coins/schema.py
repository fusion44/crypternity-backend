'''Contains all Graphql code for the coins application'''

import graphene
import celery

from graphene_django.types import DjangoObjectType

from backend.coins.models import Coin
from backend.coins.tasks import async_update_supported_coins


class CoinType(DjangoObjectType):
    '''The coin GraphQL type'''

    class Meta:
        '''The connection between the ype and the model'''
        model = Coin


class Query(object):
    '''Get all coins where user has access rights'''
    all_coins = graphene.List(CoinType)

    def resolve_all_coins(self, info):
        '''Returns all available coins'''
        if not info.context.user.is_authenticated:
            return Coin.objects.none()
        return Coin.objects.all()


class CoinRefreshTransactionsMutation(graphene.relay.ClientIDMutation):
    '''GraphQL Mutation for refreshing supported coins'''
    status = graphene.Int()
    formErrors = graphene.String()
    msg = graphene.String()

    @classmethod
    def mutate(cls, root, info, input) -> "CoinRefreshTransactionsMutation":
        '''Runs the celery background task to update the coins'''
        if not info.context.user.is_superuser:
            return CoinRefreshTransactionsMutation(
                status=403, client_mutation_id=input['client_mutation_id'])

        if hasattr(celery, "result") and celery.result.AsyncResult(
                "task_update_coins").status == "RUNNING":
            print("skipping task")
            return CoinRefreshTransactionsMutation(
                msg="Task is already running",
                status=202,
                client_mutation_id=input['client_mutation_id'])
        else:
            try:
                print("starting task")
                async_update_supported_coins.apply_async(
                    task_id="task_update_coins")
            except async_update_supported_coins.OperationalError as err:
                print("Sending task raised: %r", err)
                return CoinRefreshTransactionsMutation(
                    status=500, client_mutation_id=input['client_mutation_id'])

        return CoinRefreshTransactionsMutation(
            msg="Working",
            status=200,
            client_mutation_id=input['client_mutation_id'])
