from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Currency(models.TextChoices):
    UZS = 'UZS', 'UZS'
    USD = 'USD', 'USD'
    EUR = 'EUR', 'EUR'


class Account(models.Model):
    class Type(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Card'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts'
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=4, choices=Type.choices, default=Type.CASH)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.UZS)
    initial_balance = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal('0')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'], name='unique_account_name_per_user'
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.currency})'


class CategoryBase(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    name_uz = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100, blank=True)
    name_en = models.CharField(max_length=100, blank=True)

    class Meta:
        abstract = True
        ordering = ['name_uz', 'id']

    def label(self, lang):
        return getattr(self, f'name_{lang}', '') or self.name_uz

    def __str__(self):
        return self.name_uz


class IncomeCategory(CategoryBase):
    pass


class ExpenseCategory(CategoryBase):
    pass

class TransactionBase(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='%(class)ss'
    )
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='%(class)ss'
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-date', '-id']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='%(class)s_amount_positive',
            ),
        ]


class Income(TransactionBase):
    category = models.ForeignKey(
        IncomeCategory, on_delete=models.PROTECT, related_name='incomes'
    )

    def __str__(self):
        return f'+{self.amount} {self.account.currency}'


class Expense(TransactionBase):
    category = models.ForeignKey(
        ExpenseCategory, on_delete=models.PROTECT, related_name='expenses'
    )

    def __str__(self):
        return f'-{self.amount} {self.account.currency}'


class Transfer(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transfers'
    )
    from_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='outgoing_transfers'
    )
    to_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='incoming_transfers'
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    to_amount = models.DecimalField(max_digits=18, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(from_account=models.F('to_account')),
                name='transfer_different_accounts',
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0) & models.Q(to_amount__gt=0),
                name='transfer_amounts_positive',
            ),
        ]

    def __str__(self):
        return f'{self.from_account} -> {self.to_account}: {self.amount}'
