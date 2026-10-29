from rest_framework.routers import DefaultRouter

from .views import (
    AccountViewSet,
    ExpenseCategoryViewSet,
    ExpenseViewSet,
    IncomeCategoryViewSet,
    IncomeViewSet,
    TransferViewSet,
)

router = DefaultRouter()
router.register('accounts', AccountViewSet, basename='account')
router.register('income-categories', IncomeCategoryViewSet, basename='income-category')
router.register('expense-categories', ExpenseCategoryViewSet, basename='expense-category')
router.register('incomes', IncomeViewSet, basename='income')
router.register('expenses', ExpenseViewSet, basename='expense')
router.register('transfers', TransferViewSet, basename='transfer')

urlpatterns = router.urls