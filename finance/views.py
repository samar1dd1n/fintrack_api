from django.db.models import ProtectedError, Q
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from .models import Account, Expense, ExpenseCategory, Income, IncomeCategory, Transfer
from .permissions import CategoryPermission
from .serializers import (
    AccountSerializer,
    ExpenseCategorySerializer,
    ExpenseSerializer,
    IncomeCategorySerializer,
    IncomeSerializer,
    TransferSerializer,
)
from .services import annotate_balance


class OwnedQuerysetMixin:


    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, 'swagger_fake_view', False):
            return queryset.none()
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProtectedDeleteMixin:


    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': 'Cannot delete: it is used by other records.'},
                status=status.HTTP_409_CONFLICT,
            )


class AccountViewSet(OwnedQuerysetMixin, ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        return annotate_balance(super().get_queryset())


class CategoryViewSetBase(ProtectedDeleteMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CategoryPermission]
    search_fields = ['name_uz', 'name_ru', 'name_en']

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, 'swagger_fake_view', False):
            return queryset.none()
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(Q(user=user) | Q(user__isnull=True))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IncomeCategoryViewSet(CategoryViewSetBase):
    queryset = IncomeCategory.objects.all()
    serializer_class = IncomeCategorySerializer


class ExpenseCategoryViewSet(CategoryViewSetBase):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer


class IncomeViewSet(OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Income.objects.select_related('account', 'category')
    serializer_class = IncomeSerializer
    search_fields = ['note']
    ordering_fields = ['date', 'amount', 'created_at']


class ExpenseViewSet(OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Expense.objects.select_related('account', 'category')
    serializer_class = ExpenseSerializer
    search_fields = ['note']
    ordering_fields = ['date', 'amount', 'created_at']


class TransferViewSet(OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Transfer.objects.select_related('from_account', 'to_account')
    serializer_class = TransferSerializer
    search_fields = ['note']
    ordering_fields = ['date', 'amount', 'created_at']


