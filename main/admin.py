from django.contrib import admin
from django import forms
from django.contrib import messages
from django.utils.html import format_html
from decimal import Decimal
from django.shortcuts import render, redirect
from django.urls import path
from django.db import transaction

from .models import User, BalanceAdjustmentLog,About,Video,Help,Notification,UserProfile


admin.site.register(About)
admin.site.register(Video)
admin.site.register(Help)
admin.site.register(Notification)
admin.site.register(UserProfile)


class BalanceAdjustmentForm(forms.Form):
    FUND_TYPES = (
        ('php_invest', 'PHP Invest Total'),
        ('php_reit', 'PHP REIT Fund Total'),
    )

    ADJUSTMENT_TYPES = (
        ('increase', 'Increase'),
        ('decrease', 'Decrease'),
    )

    fund_type = forms.ChoiceField(choices=FUND_TYPES, label="Fund Type")
    percentage = forms.DecimalField(max_digits=6, decimal_places=2, min_value=0.01, max_value=100, label="Percentage")
    adjustment_type = forms.ChoiceField(choices=ADJUSTMENT_TYPES, label="Adjustment Type")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
    'username', 'phone_number', 'php_invest_display', 'php_reit_display', 'total_balance_display', 'is_active')
    search_fields = ('username', 'phone_number', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff')

    def php_invest_display(self, obj):
        return obj.get_formatted_balance('php_invest')

    php_invest_display.short_description = 'PHP Invest Balance'

    def php_reit_display(self, obj):
        return obj.get_formatted_balance('php_reit')

    php_reit_display.short_description = 'PHP REIT Balance'

    def total_balance_display(self, obj):
        return obj.get_formatted_balance()

    total_balance_display.short_description = 'Total Balance'


@admin.register(BalanceAdjustmentLog)
class BalanceAdjustmentLogAdmin(admin.ModelAdmin):
    list_display = (
    'fund_type_display', 'percentage_display', 'adjustment_type', 'admin', 'timestamp', 'affected_users_count')
    list_filter = ('fund_type', 'adjustment_type', 'timestamp')
    search_fields = ('admin__username',)
    readonly_fields = ('admin', 'fund_type', 'percentage', 'adjustment_type', 'timestamp', 'affected_users_count')

    def fund_type_display(self, obj):
        return obj.get_fund_type_display()

    fund_type_display.short_description = 'Fund Type'

    def percentage_display(self, obj):
        color = 'green' if obj.adjustment_type == 'increase' else 'red'
        sign = '+' if obj.adjustment_type == 'increase' else '-'
        return format_html('<span style="color: {};">{}{:.2f}%</span>', color, sign, obj.percentage)

    percentage_display.short_description = 'Percentage'

    def has_add_permission(self, request):
        return False


# class BalanceAdjustmentAdmin(admin.ModelAdmin):
#     change_list_template = 'admin/balance_adjustment.html'
#
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('adjust-balance/', self.adjust_balance_view, name='adjust-balance'),
#         ]
#         return custom_urls + urls
#
#     @transaction.atomic
#     def apply_adjustment(self, request, form):
#         fund_type = form.cleaned_data['fund_type']
#         percentage = form.cleaned_data['percentage']
#         adjustment_type = form.cleaned_data['adjustment_type']
#
#         users = User.objects.filter(is_active=True)
#         affected_users = 0
#
#         for user in users:
#             if fund_type == 'php_invest':
#                 previous_balance = user.php_invest_balance
#                 adjustment_amount = (previous_balance * Decimal(percentage) / Decimal(100))
#
#                 if adjustment_type == 'increase':
#                     user.php_invest_balance += adjustment_amount
#                 else:  # decrease
#                     user.php_invest_balance -= adjustment_amount
#                     # Ensure balance doesn't go below zero
#                     if user.php_invest_balance < 0:
#                         user.php_invest_balance = Decimal('0.00')
#
#                 user.save()
#                 affected_users += 1
#
#             elif fund_type == 'php_reit':
#                 previous_balance = user.php_reit_balance
#                 adjustment_amount = (previous_balance * Decimal(percentage) / Decimal(100))
#
#                 if adjustment_type == 'increase':
#                     user.php_reit_balance += adjustment_amount
#                 else:  # decrease
#                     user.php_reit_balance -= adjustment_amount
#                     # Ensure balance doesn't go below zero
#                     if user.php_reit_balance < 0:
#                         user.php_reit_balance = Decimal('0.00')
#
#                 user.save()
#                 affected_users += 1
#
#         # Log the adjustment
#         log = BalanceAdjustmentLog.objects.create(
#             admin=request.user,
#             fund_type=fund_type,
#             percentage=percentage,
#             adjustment_type=adjustment_type,
#             affected_users_count=affected_users
#         )
#
#         return affected_users
#
#     def adjust_balance_view(self, request):
#         if request.method == 'POST':
#             form = BalanceAdjustmentForm(request.POST)
#             if form.is_valid():
#                 affected_users = self.apply_adjustment(request, form)
#                 self.message_user(
#                     request,
#                     f"Successfully adjusted balances for {affected_users} users.",
#                     messages.SUCCESS
#                 )
#                 return redirect('admin:index')
#         else:
#             form = BalanceAdjustmentForm()
#
#         context = {
#             'form': form,
#             'title': 'Adjust User Balances',
#             'opts': self.model._meta,
#         }
#         return render(request, 'admin/balance_adjustment_form.html', context)


# Admin saytiga Balance Adjustment sahifasini qo'shish
# admin.site.register(BalanceAdjustmentAdmin)

