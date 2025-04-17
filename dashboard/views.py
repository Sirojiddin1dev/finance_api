from http.client import responses
from django.shortcuts import render
from django.template.defaultfilters import first
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from main.models import Notification, About , Video , Help, UserProfile, User
from main.serializers import NotificationSerializer, AboutSerializer, VideoSerializer, HelpSerializer, UserProfileSerializer
from rest_framework.decorators import api_view, permission_classes
from drf_yasg import openapi



@swagger_auto_schema(
    method='get',
    responses={200: NotificationSerializer(many=True)}
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_notification(request):
    notifications = Notification.objects.filter(user=request.user)
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data, status=200)


@swagger_auto_schema(
    method = 'get',
    response = { 200: NotificationSerializer}
)

@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_user_notifications(request, pk):
    try:
        notification = Notification.objects.get(pk=pk)
    except Notification.DoesNotExist:
        return Response({"error": "Bildirishnoma topilmadi."}, status=status.HTTP_404_NOT_FOUND)
    serializer = NotificationSerializer(notification)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method ='get',
    response = { 200: AboutSerializer }
)

@api_view(['GET'])
def get_about(request):
    try:
        about = About.objects.last()
    except About.DoesNotExist:
        return Response({"error": "Ma'lumot topilmadi."}, status=status.HTTP_404_NOT_FOUND)

    serializer = AboutSerializer(about)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method ='get',
    response  = { 200: HelpSerializer }
)

@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_help(request):
    try:
        help_info = Help.objects.last()
    except Help.DoesNotExist:
        return Response({"error": "Ma'lumot topilmadi."}, status=status.HTTP_404_NOT_FOUND)

    serializer = HelpSerializer(help_info)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method ='get',
    response = { 200: VideoSerializer },
)

@api_view(['GET'])
def get_videos(request):
    videos = Video.objects.all().order_by('-id')
    serializer = VideoSerializer(videos, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



@swagger_auto_schema(
    method ='get',
    response ={200: VideoSerializer}
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_video_detail(request, pk):
    try:
        video = Video.objects.get(pk=pk),first()
    except Video.DoesNotExist:
        return Response({"detail": "Video topilmadi."}, status=404)

    serializer = VideoSerializer(video)
    return Response(serializer.data, status=200)


# @swagger_auto_schema(
#     method ='get',
#     response ={200: UserProfile}
# )
#
# @swagger_auto_schema(
#     method ='post',
#     response ={200: UserProfile}
# )
#
# @api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])
# def user_profile_list_create(request):
#     if request.method == 'GET':
#         profiles = UserProfile.objects.all()
#         serializer = UserProfileSerializer(profiles, many=True)
#         return Response(serializer.data)
#
#     elif request.method == 'POST':
#         serializer = UserProfileSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# @swagger_auto_schema(
#     method ='get',
#     response ={200: UserProfile}
# )
#
# @swagger_auto_schema(
#     method ='put',
#     response ={200: UserProfile}
# )
#
# @swagger_auto_schema(
#     method ='delete',
#     response ={200: UserProfile}
# )
#
# @api_view(['GET', 'PUT', 'DELETE'])
# @permission_classes([IsAuthenticated])
# def user_profile_detail(request, pk):
#     try:
#         profile = UserProfile.objects.get(pk=pk)
#     except UserProfile.DoesNotExist:
#         return Response({'error': 'Profile topilmadi'}, status=status.HTTP_404_NOT_FOUND)
#
#     if request.method == 'GET':
#         serializer = UserProfileSerializer(profile)
#         return Response(serializer.data)
#
#     elif request.method == 'PUT':
#         serializer = UserProfileSerializer(profile, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     elif request.method == 'DELETE':
#         profile.delete()
#         return Response({'message': 'Profil o‘chirildi'}, status=status.HTTP_204_NO_CONTENT)