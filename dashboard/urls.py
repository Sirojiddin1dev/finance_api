from django.urls import path
from .views import get_help, get_videos, get_about, get_user_notifications,get_video_detail

urlpatterns = [
    path('help/', get_help, name='get_help'),
    path('video/', get_videos, name='get_videos'),
    path('about/', get_about, name='get_about'),
    path('get_user_notifications/<int:pk>/', get_user_notifications, name='get_user_notifications'),
    path('videos/<int:pk>/', get_video_detail, name = 'get_video_detail'),

]
