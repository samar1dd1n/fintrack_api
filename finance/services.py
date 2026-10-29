from decimal import Decimal

from django.db.models import DecimalField, F, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from .models import Expense, Income, Transfer

ZERO = Value(Decimal('0'), output_field=DecimalField(max_digits=18, decimal_places=2))


def _total(model, amount_field, account_field):
    return Coalesce(
        Subquery(
            model.objects.filter(**{account_field: OuterRef('pk')})
            .order_by()
            .values(account_field)
            .annotate(total=Sum(amount_field))
            .values('total')
        ),
        ZERO,
    )


def annotate_balance(accounts):
    return accounts.annotate(
        income_total=_total(Income, 'amount', 'account'),
        expense_total=_total(Expense, 'amount', 'account'),
        transfer_out=_total(Transfer, 'amount', 'from_account'),
        transfer_in=_total(Transfer, 'to_amount', 'to_account'),
    ).annotate(
        balance=(
                F('initial_balance')
                + F('income_total')
                - F('expense_total')
                + F('transfer_in')
                - F('transfer_out')
        )
    )