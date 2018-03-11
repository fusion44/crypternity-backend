'''Contains all Graphql code for the coins application'''

import graphene

from graphene_django.types import DjangoObjectType

from backend.coins.models import Coin


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
