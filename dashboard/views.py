from django.shortcuts import render
from main.models import Notification, About , Video , Help, UserProfile
from main.serializers import NotificationSerializer, AboutSerializer, VideoSerializer, HelpSerializer, UserProfileSerializer
from rest_framework.generics import ListAPIView

class NotificationView(ListAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer


class AboutView(ListAPIView):
    queryset = About.objects.all()
    serializer_class = AboutSerializer


class VideoView(ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class HelpView(ListAPIView):
    queryset = Help.objects.all()
    serializer_class = HelpSerializer


class UserProfileView(ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

