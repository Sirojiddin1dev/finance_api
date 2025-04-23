from django.urls import path
from .views import get_help, get_videos, get_about,get_video_detail,get_user_notifications,get_user_notification,get_user_profile,edit_user_profile_view

urlpatterns = [
    path('help/', get_help, name='get_help'),
    path('video/', get_videos, name='get_videos'),
    path('about/', get_about, name='get_about'),
    path('get_user_notification_detail/', get_user_notification, name='get_user_notification_detail'),
    path('get_user_notifications/<int:pk>/', get_user_notifications, name='get_user_notifications'),
    path('videos/<int:pk>/', get_video_detail, name = 'get_video_detail'),
    path('user/profile/', get_user_profile, name='user-profile'),
    path('user/profile/update/', edit_user_profile_view, name='user-profile-update'),

]
