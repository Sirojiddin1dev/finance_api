from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from main.serializers import *


class UserBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view user balances
    """
    queryset = User.objects.all()
    serializer_class = UserBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter to only return the authenticated user's balance
        """
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)

    @swagger_auto_schema(
        operation_description="Get current user's balance information",
        responses={200: UserBalanceSerializer()}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Return the authenticated user's balance
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class BalanceAdjustmentLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view balance adjustment history
    """
    queryset = BalanceAdjustmentLog.objects.all().order_by('-timestamp')
    serializer_class = BalanceAdjustmentLogSerializer
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="Get recent balance adjustments",
        responses={200: BalanceAdjustmentLogSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Return the 10 most recent balance adjustments
        """
        recent_adjustments = BalanceAdjustmentLog.objects.all().order_by('-timestamp')[:10]
        serializer = self.get_serializer(recent_adjustments, many=True)
        return Response(serializer.data)


class BalanceAdjustmentAPIView(APIView):
    """
    API endpoint to apply percentage adjustments to user balances
    """
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="Apply percentage adjustment to user balances",
        request_body=BalanceAdjustmentSerializer,
        responses={
            200: openapi.Response(
                description="Adjustment applied successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'affected_users': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            400: "Bad request"
        }
    )
    @transaction.atomic
    def post(self, request):
        """
        Apply percentage adjustment to user balances
        """
        serializer = BalanceAdjustmentSerializer(data=request.data)
        if serializer.is_valid():
            fund_type = serializer.validated_data['fund_type']
            percentage = serializer.validated_data['percentage']
            adjustment_type = serializer.validated_data['adjustment_type']

            # Filter users with balance > 0 for the specified fund type
            if fund_type == 'php_invest':
                users = User.objects.filter(php_invest_balance__gt=0)
            else:  # php_reit
                users = User.objects.filter(php_reit_balance__gt=0)

            affected_users = 0

            for user in users:
                if fund_type == 'php_invest':
                    previous_balance = user.php_invest_balance
                    adjustment_amount = (previous_balance * Decimal(percentage) / Decimal(100))

                    if adjustment_type == 'increase':
                        user.php_invest_balance += adjustment_amount
                    else:  # decrease
                        user.php_invest_balance -= adjustment_amount
                        # Ensure balance doesn't go below zero
                        if user.php_invest_balance < 0:
                            user.php_invest_balance = Decimal('0.00')

                    user.save()
                    affected_users += 1

                elif fund_type == 'php_reit':
                    previous_balance = user.php_reit_balance
                    adjustment_amount = (previous_balance * Decimal(percentage) / Decimal(100))

                    if adjustment_type == 'increase':
                        user.php_reit_balance += adjustment_amount
                    else:  # decrease
                        user.php_reit_balance -= adjustment_amount
                        # Ensure balance doesn't go below zero
                        if user.php_reit_balance < 0:
                            user.php_reit_balance = Decimal('0.00')

                    user.save()
                    affected_users += 1

            # Log the adjustment
            log = BalanceAdjustmentLog.objects.create(
                admin=request.user,
                fund_type=fund_type,
                percentage=percentage,
                adjustment_type=adjustment_type,
                affected_users_count=affected_users
            )

            return Response({
                'success': True,
                'message': f"Successfully adjusted balances for {affected_users} users.",
                'affected_users': affected_users
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBalanceStatisticsAPIView(APIView):
    """
    API endpoint to get statistics about user balances
    """
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="Get statistics about user balances",
        responses={200: UserBalanceStatisticsSerializer()}
    )
    def get(self, request):
        """
        Get statistics about user balances
        """
        total_users = User.objects.count()
        users_with_balance = User.objects.filter(
            Q(php_invest_balance__gt=0) | Q(php_reit_balance__gt=0)
        ).count()

        total_php_invest = User.objects.aggregate(Sum('php_invest_balance'))['php_invest_balance__sum'] or 0
        total_php_reit = User.objects.aggregate(Sum('php_reit_balance'))['php_reit_balance__sum'] or 0
        total_balance = total_php_invest + total_php_reit

        average_balance = 0
        if users_with_balance > 0:
            average_balance = total_balance / users_with_balance

        data = {
            'total_users': total_users,
            'users_with_balance': users_with_balance,
            'total_php_invest': total_php_invest,
            'total_php_reit': total_php_reit,
            'total_balance': total_balance,
            'average_balance': average_balance
        }

        serializer = UserBalanceStatisticsSerializer(data)
        return Response(serializer.data)


class MonthlyBalanceAPIView(APIView):
    """
    API endpoint to get monthly balance data for charts
    """
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="Get monthly balance data for the last 6 months",
        responses={200: MonthlyBalanceSerializer(many=True)}
    )
    def get(self, request):
        """
        Get monthly balance data for the last 6 months
        """
        # Get data for the last 6 months
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=180)  # Approximately 6 months

        # Get all adjustment logs in this period
        logs = BalanceAdjustmentLog.objects.filter(
            timestamp__date__range=[start_date, end_date]
        ).order_by('timestamp')

        # Group by month
        monthly_data = []
        current_date = start_date

        while current_date <= end_date:
            month_name = current_date.strftime('%b %Y')
            month_start = datetime(current_date.year, current_date.month, 1)

            if current_date.month == 12:
                next_month = datetime(current_date.year + 1, 1, 1)
            else:
                next_month = datetime(current_date.year, current_date.month + 1, 1)

            # Get all users' balances at the end of this month
            # For a real implementation, you would need to track balance history
            # This is a simplified version that uses current balances
            php_invest_total = User.objects.aggregate(Sum('php_invest_balance'))['php_invest_balance__sum'] or 0
            php_reit_total = User.objects.aggregate(Sum('php_reit_balance'))['php_reit_balance__sum'] or 0
            total_balance = php_invest_total + php_reit_total

            monthly_data.append({
                'month': month_name,
                'php_invest_total': php_invest_total,
                'php_reit_total': php_reit_total,
                'total_balance': total_balance
            })

            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        serializer = MonthlyBalanceSerializer(monthly_data, many=True)
        return Response(serializer.data)

