from rest_framework import serializers
from .models import *
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import serializers
from .models import User

class UserAvatarNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['avatar', 'push_notifications']


class UserBalanceSerializer(serializers.ModelSerializer):
    total_balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'phone_number', 'php_invest_balance', 'php_reit_balance', 'total_balance']
        read_only_fields = ['id', 'username', 'phone_number', 'php_invest_balance', 'php_reit_balance', 'total_balance']


class BalanceAdjustmentLogSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    fund_type_display = serializers.CharField(source='get_fund_type_display', read_only=True)

    class Meta:
        model = BalanceAdjustmentLog
        fields = ['id', 'admin_username', 'fund_type', 'fund_type_display', 'percentage',
                  'adjustment_type', 'timestamp', 'affected_users_count']
        read_only_fields = ['id', 'admin_username', 'timestamp', 'affected_users_count']


class BalanceAdjustmentSerializer(serializers.Serializer):
    FUND_TYPES = (
        ('php_invest', 'PHP Invest Total'),
        ('php_reit', 'PHP REIT Fund Total'),
    )

    ADJUSTMENT_TYPES = (
        ('increase', 'Increase'),
        ('decrease', 'Decrease'),
    )

    fund_type = serializers.ChoiceField(choices=FUND_TYPES)
    percentage = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0.01, max_value=100)
    adjustment_type = serializers.ChoiceField(choices=ADJUSTMENT_TYPES)


class UserBalanceStatisticsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    users_with_balance = serializers.IntegerField()
    total_php_invest = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_php_reit = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_balance = serializers.DecimalField(max_digits=15, decimal_places=2)


class MonthlyBalanceSerializer(serializers.Serializer):
    month = serializers.CharField()
    php_invest_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    php_reit_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_balance = serializers.DecimalField(max_digits=15, decimal_places=2)


# class PaymentCardSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PaymentCard
#         fields = ['id', 'card_number', 'expiry_date', 'is_main']
#         read_only_fields = ['user']
#
#     def create(self, validated_data):
#         if validated_data.get('is_main'):
#             PaymentCard.objects.filter(
#                 user=self.context['request'].user,
#                 is_main=True
#             ).update(is_main=False)
#         return super().create(validated_data)


class DailyTransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_type = serializers.CharField(source='category.type', read_only=True)

    class Meta:
        model = DailyTransaction
        fields = ['id', 'category', 'category_name', 'category_type',
                  'amount', 'date', 'created_at']
        read_only_fields = ['user']


# class InvestmentSerializer(serializers.ModelSerializer):
#     card_number = serializers.CharField(source='card.card_number', read_only=True)
#     type_display = serializers.CharField(source='get_type_display', read_only=True)
#     status_display = serializers.CharField(source='get_status_display', read_only=True)
#
#     class Meta:
#         model = Investment
#         fields = ['id', 'type', 'type_display', 'card', 'card_number',
#                   'amount', 'status', 'status_display', 'description',
#                   'date', 'created_at']
#         read_only_fields = ['user', 'status']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'img', 'message', 'is_read', 'created_at']
        read_only_fields = ['user']


class AboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = About
        fields = ['text']


class HelpSerializer(serializers.ModelSerializer):
    class Meta:
        model = Help
        fields = ['telegram', 'call']


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['id', 'title', 'video', 'description']