from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'balances', UserBalanceViewSet)
router.register(r'adjustment-logs', BalanceAdjustmentLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('adjust-balance/', BalanceAdjustmentAPIView.as_view(), name='adjust-balance'),
    path('statistics/', UserBalanceStatisticsAPIView.as_view(), name='balance-statistics'),
    path('monthly-data/', MonthlyBalanceAPIView.as_view(), name='monthly-data'),
]