import json
import graphene

from graphene_django.types import DjangoObjectType

from django.contrib.auth.models import User


class UserType(DjangoObjectType):
    class Meta:
        model = User


class Query(object):
    '''Query class for everything related to users'''
    get_current_user = graphene.Field(UserType)

    def resolve_get_current_user(self, info):
        '''Returns the current user if authenticated, None otherwise'''
        if not info.context.user.is_authenticated:
            return None
        return info.context.user
