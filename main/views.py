# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .token import get_tokens_for_user

User = get_user_model()

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class RegisterAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Yangi foydalanuvchini ro'yxatdan o'tkazish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['full_name', 'email', 'password'],
            properties={
                'full_name': openapi.Schema(type=openapi.TYPE_STRING, description="Foydalanuvchining to'liq ismi"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Foydalanuvchining email manzili"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format="password", description="Parol"),
            }
        ),
        responses={
            201: openapi.Response(
                description="Foydalanuvchi muvaffaqiyatli yaratildi",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'token': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    }
                )
            ),
            400: "Bad request (Email band bo'lishi mumkin)",
        }
    )
    def post(self, request):
        data = request.data
        email = data.get("email")
        password = data.get("password")
        first_name = data.get("first_name")
        last_name = data.get("last_name")

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email allaqachon mavjud"}, status=400)

        user = User.objects.create(
            email=email,
            username=email,
            first_name=first_name,
            last_name=last_name,
            password=make_password(password),
            is_active=True,
        )
        tokens = get_tokens_for_user(user)

        return Response({
            "message": "Foydalanuvchi muvaffaqiyatli yaratildi",
            "token": tokens
        }, status=201)


from django.contrib.auth import authenticate

class LoginAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Email va parol orqali login qilish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Foydalanuvchi emaili"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format="password", description="Foydalanuvchi paroli"),
            }
        ),
        responses={
            200: openapi.Response(
                description="Login muvaffaqiyatli",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'token': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    }
                )
            ),
            400: "Noto'g'ri email yoki parol",
        }
    )
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({"error": "Noto‘g‘ri email yoki parol"}, status=400)

        tokens = get_tokens_for_user(user)
        return Response({"message": "Kirish muvaffaqiyatli", "token": tokens})



import random
from django.core.cache import cache
from django.core.mail import send_mail

class ForgotPasswordAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Parolni tiklash uchun emailga kod yuborish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Foydalanuvchining email manzili"),
            }
        ),
        responses={
            200: "Kod yuborildi",
            404: "Foydalanuvchi topilmadi"
        }
    )
    def post(self, request):
        email = request.data.get("email")
        if not User.objects.filter(email=email).exists():
            return Response({"error": "Email topilmadi"}, status=404)

        code = str(random.randint(100000, 999999))
        cache.set(f"reset_code_{email}", code, timeout=300)

        # Email jo‘natish
        send_mail(
            "Parolni tiklash kodi",
            f"Sizning parolni tiklash kodingiz: {code}",
            "noreply@yourapp.com",
            [email],
            fail_silently=False
        )

        return Response({"message": "Kod yuborildi"})


class ResetPasswordAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Yuborilgan kodni tasdiqlab yangi parol o'rnatish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'code', 'new_password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Foydalanuvchining email manzili"),
                'code': openapi.Schema(type=openapi.TYPE_STRING, description="Emailga yuborilgan kod"),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, format="password", description="Yangi parol"),
            }
        ),
        responses={
            200: "Parol yangilandi",
            400: "Kod noto'g'ri yoki muddati tugagan"
        }
    )
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        new_password = request.data.get("new_password")

        cached_code = cache.get(f"reset_code_{email}")
        if cached_code != code:
            return Response({"error": "Noto‘g‘ri kod"}, status=400)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            cache.delete(f"reset_code_{email}")
            return Response({"message": "Parol muvaffaqiyatli yangilandi"})
        except User.DoesNotExist:
            return Response({"error": "Foydalanuvchi topilmadi"}, status=404)






















# from rest_framework.response import Response
# from rest_framework import status
# from django.contrib.auth import authenticate, login, logout
# from rest_framework.permissions import IsAuthenticated
# from .token import get_tokens_for_user
# import random
# from django.core.cache import cache
# from django.contrib.auth import get_user_model
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
# from .utils import send_sms_eskiz
# from rest_framework.exceptions import AuthenticationFailed
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework_simplejwt.tokens import RefreshToken
#
# User = get_user_model()
#
#
# def send_otp(phone_number):
#     otp = str(random.randint(100000, 999999))
#     message = f"Prime Haven Properties Saytiga kirish uchun sizning tasdiqlash kodingiz: {otp}"
#     success = send_sms_eskiz(phone_number, message)
#     if success:
#         cache.set(f"otp_{phone_number}", otp, timeout=300)
#         return otp
#     return None
#
# class SignupInitiateAPIView(APIView):
#     @swagger_auto_schema(
#         operation_description="Initiate user registration",
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=['phone_number'],
#             properties={
#                 'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="User's phone number"),
#             },
#         ),
#         responses={
#             200: openapi.Response(
#                 description="OTP sent successfully",
#                 schema=openapi.Schema(
#                     type=openapi.TYPE_OBJECT,
#                     properties={
#                         'status': openapi.Schema(type=openapi.TYPE_INTEGER),
#                         'message': openapi.Schema(type=openapi.TYPE_STRING),
#                         'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
#                     },
#                 ),
#             ),
#             400: "Bad Request",
#             500: "Internal Server Error - SMS yuborishda xatolik",
#         },
#     )
#     def post(self, request):
#         phone_number = request.data.get('phone_number')
#
#         if not phone_number:
#             return Response({
#                 'status': 400,
#                 'message': 'Telefon raqami talab qilinadi'
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         if User.objects.filter(phone_number=phone_number).exists():
#             return Response({
#                 'status': 400,
#                 'message': 'Bu telefon raqami allaqachon ro\'yxatdan o\'tgan'
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         otp = send_otp(phone_number)
#         if otp is None:
#             return Response({
#                 'status': 500,
#                 'message': 'SMS yuborishda xatolik yuz berdi',
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#         return Response({
#             'status': 200,
#             'message': 'Tasdiqlash kodi yuborildi',
#             'phone_number': phone_number
#         }, status=status.HTTP_200_OK)
#
# class SignupCompleteAPIView(APIView):
#     @swagger_auto_schema(
#         operation_description="Complete user registration",
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=['phone_number', 'otp', 'first_name', 'last_name'],
#             properties={
#                 'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="User's phone number"),
#                 'otp': openapi.Schema(type=openapi.TYPE_STRING, description="OTP received by user"),
#                 'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="User's first name"),
#                 'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="User's last name"),
#             },
#         ),
#         responses={
#             200: openapi.Response(
#                 description="User registered successfully",
#                 schema=openapi.Schema(
#                     type=openapi.TYPE_OBJECT,
#                     properties={
#                         'status': openapi.Schema(type=openapi.TYPE_INTEGER),
#                         'message': openapi.Schema(type=openapi.TYPE_STRING),
#                         'token': openapi.Schema(type=openapi.TYPE_OBJECT),
#                     },
#                 ),
#             ),
#             400: "Bad Request",
#             404: "Not Found",
#         },
#     )
#     def post(self, request):
#         phone_number = request.data.get('phone_number')
#         otp = request.data.get('otp')
#         first_name = request.data.get('first_name')
#         last_name = request.data.get('last_name')
#
#         if not all([phone_number, otp, first_name, last_name]):
#             return Response({
#                 'status': 400,
#                 'message': 'Barcha ma\'lumotlar talab qilinadi'
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         stored_otp = cache.get(f"otp_{phone_number}")
#         if not stored_otp or otp != stored_otp:
#             return Response({
#                 'status': 400,
#                 'message': 'Noto\'g\'ri OTP'
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         user = User.objects.create_user(
#             username=phone_number,
#             phone_number=phone_number,
#             first_name=first_name,
#             last_name=last_name
#         )
#         user.is_active = True
#         user.is_phone_verified = True
#         user.save()
#
#         tokens = get_tokens_for_user(user)
#         cache.delete(f"otp_{phone_number}")
#
#         return Response({
#             'status': 200,
#             'message': 'Foydalanuvchi muvaffaqiyatli ro\'yxatdan o\'tdi',
#             'token': tokens
#         }, status=status.HTTP_200_OK)
#
# class LoginInitiateAPIView(APIView):
#     @swagger_auto_schema(
#         operation_description="Initiate login process",
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=['phone_number'],
#             properties={
#                 'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="User's phone number"),
#             },
#         ),
#         responses={
#             200: openapi.Response(
#                 description="Login OTP sent successfully",
#                 schema=openapi.Schema(
#                     type=openapi.TYPE_OBJECT,
#                     properties={
#                         'status': openapi.Schema(type=openapi.TYPE_INTEGER),
#                         'message': openapi.Schema(type=openapi.TYPE_STRING),
#                         'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
#                     },
#                 ),
#             ),
#             400: "Bad Request",
#             404: "Not Found",
#             500: "Internal Server Error - SMS yuborishda xatolik",
#         },
#     )
#     def post(self, request):
#         phone_number = request.data.get('phone_number')
#
#         if not phone_number:
#             return Response({
#                 'status': 400,
#                 'message': 'Telefon raqami talab qilinadi'
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         try:
#             user = User.objects.get(phone_number=phone_number)
#         except User.DoesNotExist:
#             return Response({
#                 'status': 404,
#                 'message': 'Foydalanuvchi topilmadi'
#             }, status=status.HTTP_404_NOT_FOUND)
#
#         otp = send_otp(phone_number)
#         if otp is None:
#             return Response({
#                 'status': 500,
#                 'message': 'SMS yuborishda xatolik yuz berdi'
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#         return Response({
#             'status': 200,
#             'message': 'Tasdiqlash kodi yuborildi',
#             'phone_number': phone_number
#         }, status=status.HTTP_200_OK)
#
# class LoginCompleteAPIView(APIView):
#     @swagger_auto_schema(
#         operation_description="Complete login process",
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=['phone_number', 'otp'],
#             properties={
#                 'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="User's phone number"),
#                 'otp': openapi.Schema(type=openapi.TYPE_STRING, description="OTP received by user"),
#             },
#         ),
#         responses={
#             200: openapi.Response(
#                 description="Login completed successfully",
#                 schema=openapi.Schema(
#                     type=openapi.TYPE_OBJECT,
#                     properties={
#                         'status': openapi.Schema(type=openapi.TYPE_INTEGER),
#                         'message': openapi.Schema(type=openapi.TYPE_STRING),
#                         'token': openapi.Schema(type=openapi.TYPE_OBJECT),
#                     },
#                 ),
#             ),
#             400: "Bad Request",
#             404: "Not Found",
#         },
#     )
#     def post(self, request):
#         phone_number = request.data.get('phone_number')
#         otp = request.data.get('otp')
#
#         if not phone_number or not otp:
#             return Response({
#                 'status': 400,
#                 'message': 'Telefon raqami va OTP talab qilinadi'
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         stored_otp = cache.get(f"otp_{phone_number}")
#         if not stored_otp or otp != stored_otp:
#             return Response({
#                 'status': 400,
#                 'message': 'Noto\'g\'ri yoki muddati o\'tgan OTP'
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         try:
#             user = User.objects.get(phone_number=phone_number)
#         except User.DoesNotExist:
#             return Response({
#                 'status': 404,
#                 'message': 'Foydalanuvchi topilmadi'
#             }, status=status.HTTP_404_NOT_FOUND)
#
#         login(request, user)
#         tokens = get_tokens_for_user(user)
#         cache.delete(f"otp_{phone_number}")
#
#         return Response({
#             'status': 200,
#             'message': 'Muvaffaqiyatli login qilindi',
#             'token': tokens
#         }, status=status.HTTP_200_OK)
#
# @swagger_auto_schema(
#     method='post',
#     request_body=openapi.Schema(
#         type=openapi.TYPE_OBJECT,
#         required=['refresh'],
#         properties={
#             'refresh': openapi.Schema(type=openapi.TYPE_STRING),
#         },
#     ),
#     responses={
#         200: 'OK',
#         400: 'Bad Request'
#     }
# )
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def logout_view(request):
#     try:
#         token = request.data.get("refresh")
#         if token:
#             refresh_token = RefreshToken(token)
#             refresh_token.blacklist()
#         return Response({"message": "Foydalanuvchi tizimdan chiqdi."}, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#
