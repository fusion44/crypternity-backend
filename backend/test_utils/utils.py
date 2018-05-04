import pytest

import random
from faker import Faker
from mixer.backend.django import mixer

from django.utils import timezone

from graphql.execution.base import ResolveInfo

from backend.transactions.models import Transaction

pytestmark = pytest.mark.django_db


def mock_resolve_info(req) -> ResolveInfo:
    return ResolveInfo(None, None, None, None, None, None, None, None, None,
                       req)


def gen_fake_transaction(owner=None,
                         date=None,
                         spent_currency=None,
                         spent_amount=None,
                         source_peer=None,
                         acquired_currency=None,
                         acquired_amount=None,
                         target_peer=None,
                         fee_currency=None,
                         fee_amount=None,
                         book_price_btc=None,
                         book_price_eur=None,
                         tags=None) -> Transaction:
    """Generate a fake Transaction. Mixer cannot handle this class"""
    fake = Faker()
    transaction = Transaction()
    transaction.owner = owner or mixer.blend("auth.User")
    transaction.date = date or timezone.make_aware(
        fake.date_time_between(start_date="-30y", end_date="now", tzinfo=None))

    transaction.spent_currency = spent_currency or fake.cryptocurrency_code()
    transaction.spent_amount = spent_amount or random.uniform(1, 20)
    transaction.source_peer = source_peer or mixer.blend("accounts.Peer")

    transaction.acquired_currency = \
        acquired_currency or fake.cryptocurrency_code()
    transaction.acquired_amount = acquired_amount or random.uniform(1, 20)
    transaction.target_peer = target_peer or mixer.blend("accounts.Peer")

    transaction.fee_currency = fee_currency or fake.cryptocurrency_code()
    transaction.fee_amount = fee_amount or random.uniform(0, 1)
    transaction.book_price_btc = book_price_btc or random.uniform(0, 20)
    transaction.book_price_eur = book_price_eur or random.uniform(0, 50)

    transaction.save()

    if tags:
        for tag in tags:
            transaction.tags.add(tag)
        transaction.save()

    return transaction
