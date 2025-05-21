from django.urls import path
from .views import *


urlpatterns = [
    path('register/', RegisterAPIView.as_view()),
    path('login/', LoginAPIView.as_view()),
    path('forgot-password/send-code/', ForgotPasswordAPIView.as_view()),
    path('forgot-password/reset/', ResetPasswordAPIView.as_view()),
]

# urlpatterns = [
#     path('signup/initiate/', SignupInitiateAPIView.as_view(), name='signup_initiate'),
#     path('signup/complete/', SignupCompleteAPIView.as_view(), name='signup_complete'),
#     path('login/initiate/', LoginInitiateAPIView.as_view(), name='login_initiate'),
#     path('login/complete/', LoginCompleteAPIView.as_view(), name='login_complete'),
#     path('logout/', logout_view, name='logout'),
# ]
