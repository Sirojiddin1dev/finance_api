from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import IsAuthenticated
from .token import get_tokens_for_user
import random
from django.core.cache import cache
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .utils import send_sms_eskiz
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def send_otp(phone_number):
    otp = str(random.randint(100000, 999999))
    message = f"Prime Haven Properties Saytiga kirish uchun sizning tasdiqlash kodingiz: {otp}"
    success = send_sms_eskiz(phone_number, message)
    if success:
        cache.set(f"otp_{phone_number}", otp, timeout=300)
        return otp
    return None

class SignupInitiateAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Initiate user registration",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number'],
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="User's phone number"),
            },
        ),
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Bad Request",
            500: "Internal Server Error - SMS yuborishda xatolik",
        },
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({
                'status': 400,
                'message': 'Telefon raqami talab qilinadi'
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(phone_number=phone_number).exists():
            return Response({
                'status': 400,
                'message': 'Bu telefon raqami allaqachon ro\'yxatdan o\'tgan'
            }, status=status.HTTP_400_BAD_REQUEST)

        otp = send_otp(phone_number)
        if otp is None:
            return Response({
                'status': 500,
                'message': 'SMS yuborishda xatolik yuz berdi',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'status': 200,
            'message': 'Tasdiqlash kodi yuborildi',
            'phone_number': phone_number
        }, status=status.HTTP_200_OK)

class SignupCompleteAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Complete user registration",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number', 'otp', 'first_name', 'last_name'],
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="User's phone number"),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description="OTP received by user"),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="User's first name"),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="User's last name"),
            },
        ),
        responses={
            200: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'token': openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
            400: "Bad Request",
            404: "Not Found",
        },
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        if not all([phone_number, otp, first_name, last_name]):
            return Response({
                'status': 400,
                'message': 'Barcha ma\'lumotlar talab qilinadi'
            }, status=status.HTTP_400_BAD_REQUEST)

        stored_otp = cache.get(f"otp_{phone_number}")
        if not stored_otp or otp != stored_otp:
            return Response({
                'status': 400,
                'message': 'Noto\'g\'ri OTP'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=phone_number,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name
        )
        user.is_active = True
        user.is_phone_verified = True
        user.save()

        tokens = get_tokens_for_user(user)
        cache.delete(f"otp_{phone_number}")

        return Response({
            'status': 200,
            'message': 'Foydalanuvchi muvaffaqiyatli ro\'yxatdan o\'tdi',
            'token': tokens
        }, status=status.HTTP_200_OK)

class LoginInitiateAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Initiate login process",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number'],
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="User's phone number"),
            },
        ),
        responses={
            200: openapi.Response(
                description="Login OTP sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error - SMS yuborishda xatolik",
        },
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({
                'status': 400,
                'message': 'Telefon raqami talab qilinadi'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({
                'status': 404,
                'message': 'Foydalanuvchi topilmadi'
            }, status=status.HTTP_404_NOT_FOUND)

        otp = send_otp(phone_number)
        if otp is None:
            return Response({
                'status': 500,
                'message': 'SMS yuborishda xatolik yuz berdi'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'status': 200,
            'message': 'Tasdiqlash kodi yuborildi',
            'phone_number': phone_number
        }, status=status.HTTP_200_OK)

class LoginCompleteAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Complete login process",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number', 'otp'],
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="User's phone number"),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description="OTP received by user"),
            },
        ),
        responses={
            200: openapi.Response(
                description="Login completed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'token': openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
            400: "Bad Request",
            404: "Not Found",
        },
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')

        if not phone_number or not otp:
            return Response({
                'status': 400,
                'message': 'Telefon raqami va OTP talab qilinadi'
            }, status=status.HTTP_400_BAD_REQUEST)

        stored_otp = cache.get(f"otp_{phone_number}")
        if not stored_otp or otp != stored_otp:
            return Response({
                'status': 400,
                'message': 'Noto\'g\'ri yoki muddati o\'tgan OTP'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({
                'status': 404,
                'message': 'Foydalanuvchi topilmadi'
            }, status=status.HTTP_404_NOT_FOUND)

        login(request, user)
        tokens = get_tokens_for_user(user)
        cache.delete(f"otp_{phone_number}")

        return Response({
            'status': 200,
            'message': 'Muvaffaqiyatli login qilindi',
            'token': tokens
        }, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['refresh'],
        properties={
            'refresh': openapi.Schema(type=openapi.TYPE_STRING),
        },
    ),
    responses={
        200: 'OK',
        400: 'Bad Request'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        token = request.data.get("refresh")
        if token:
            refresh_token = RefreshToken(token)
            refresh_token.blacklist()
        return Response({"message": "Foydalanuvchi tizimdan chiqdi."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

