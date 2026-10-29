from django.contrib import admin

from .models import Account, Expense, ExpenseCategory, Income, IncomeCategory, Transfer


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'type', 'currency', 'initial_balance', 'created_at')
    list_filter = ('type', 'currency')
    search_fields = ('name', 'user__username')
    list_select_related = ('user',)


@admin.register(IncomeCategory, ExpenseCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_uz', 'name_ru', 'name_en', 'user', 'is_system')
    search_fields = ('name_uz', 'name_ru', 'name_en')
    list_select_related = ('user',)

    @admin.display(boolean=True, description='System')
    def is_system(self, obj):
        return obj.user_id is None


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'account', 'category', 'amount', 'currency', 'note')
    list_filter = ('date', 'account__currency')
    search_fields = ('note', 'user__username', 'account__name')
    date_hierarchy = 'date'
    list_select_related = ('user', 'account', 'category')

    @admin.display(description='Currency', ordering='account__currency')
    def currency(self, obj):
        return obj.account.currency


@admin.register(Income)
class IncomeAdmin(TransactionAdmin):
    pass


@admin.register(Expense)
class ExpenseAdmin(TransactionAdmin):
    pass


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'from_account', 'to_account', 'amount', 'to_amount', 'note')
    list_filter = ('date',)
    search_fields = ('note', 'user__username')
    date_hierarchy = 'date'
    list_select_related = ('user', 'from_account', 'to_account')