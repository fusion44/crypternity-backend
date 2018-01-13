import json
import graphene

from graphene_django.types import DjangoObjectType

from django.contrib.auth.models import User


class UserType(DjangoObjectType):
    class Meta:
        model = User


class Query(object):

    current_user = graphene.Field(UserType)

    def resolve_current_user(self, info):
        if not info.user.is_authenticated:
            return None
        return info.user
