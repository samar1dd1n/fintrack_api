from decimal import Decimal

from django.db.models import Q
from rest_framework import serializers

from .models import (
    Account,
    Expense,
    ExpenseCategory,
    Income,
    IncomeCategory,
    Transfer,
)
from .services import annotate_balance




class OwnedAccountField(serializers.PrimaryKeyRelatedField):


    def get_queryset(self):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return Account.objects.none()
        return Account.objects.filter(user=request.user)


class AvailableCategoryField(serializers.PrimaryKeyRelatedField):


    category_model = None

    def get_queryset(self):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return self.category_model.objects.none()
        return self.category_model.objects.filter(
            Q(user=request.user) | Q(user__isnull=True)
        )


class IncomeCategoryField(AvailableCategoryField):
    category_model = IncomeCategory


class ExpenseCategoryField(AvailableCategoryField):
    category_model = ExpenseCategory



def _with_balance(account):

    return annotate_balance(Account.objects.filter(pk=account.pk)).get()


class AccountSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = Account
        fields = ['id', 'name', 'type', 'currency', 'initial_balance', 'balance', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        owner = self.instance.user if self.instance else self.context['request'].user
        same_name = Account.objects.filter(user=owner, name=value)
        if self.instance:
            same_name = same_name.exclude(pk=self.instance.pk)
        if same_name.exists():
            raise serializers.ValidationError('You already have an account with this name.')
        return value

    def validate_currency(self, value):
        if self.instance and value != self.instance.currency:
            raise serializers.ValidationError('Currency cannot be changed.')
        return value

    def create(self, validated_data):
        return _with_balance(super().create(validated_data))

    def update(self, instance, validated_data):
        return _with_balance(super().update(instance, validated_data))




class CategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    system = serializers.SerializerMethodField()

    class Meta:
        fields = ['id', 'name', 'name_uz', 'name_ru', 'name_en', 'system']
        read_only_fields = ['id']

    def get_name(self, obj) -> str:
        return obj.label(self.context['request'].user.language)

    def get_system(self, obj) -> bool:
        return obj.user_id is None


class IncomeCategorySerializer(CategorySerializer):
    class Meta(CategorySerializer.Meta):
        model = IncomeCategory


class ExpenseCategorySerializer(CategorySerializer):
    class Meta(CategorySerializer.Meta):
        model = ExpenseCategory




class IncomeSerializer(serializers.ModelSerializer):
    account = OwnedAccountField()
    category = IncomeCategoryField()

    class Meta:
        model = Income
        fields = ['id', 'account', 'category', 'amount', 'date', 'note', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {'amount': {'min_value': Decimal('0.01')}}


class ExpenseSerializer(serializers.ModelSerializer):
    account = OwnedAccountField()
    category = ExpenseCategoryField()

    class Meta:
        model = Expense
        fields = ['id', 'account', 'category', 'amount', 'date', 'note', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {'amount': {'min_value': Decimal('0.01')}}




class TransferSerializer(serializers.ModelSerializer):
    from_account = OwnedAccountField()
    to_account = OwnedAccountField()

    class Meta:
        model = Transfer
        fields = [
            'id', 'from_account', 'to_account', 'amount', 'to_amount',
            'date', 'note', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'amount': {'min_value': Decimal('0.01')},
            'to_amount': {'min_value': Decimal('0.01'), 'required': False},
        }

    def validate(self, attrs):
        current = self.instance
        from_acc = attrs.get('from_account', current.from_account if current else None)
        to_acc = attrs.get('to_account', current.to_account if current else None)
        amount = attrs.get('amount', current.amount if current else None)
        to_amount = attrs.get('to_amount')

        if from_acc == to_acc:
            raise serializers.ValidationError(
                {'to_account': 'Source and destination accounts must differ.'}
            )

        if from_acc.currency == to_acc.currency:
            if to_amount is not None and to_amount != amount:
                raise serializers.ValidationError(
                    {'to_amount': 'Must equal amount when both accounts have the same currency.'}
                )
            attrs['to_amount'] = amount
        elif to_amount is None and current is None:
            raise serializers.ValidationError(
                {'to_amount': 'Required when accounts have different currencies.'}
            )
        return attrs