import random, time
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User


# Create your views here.

class LoginView(APIView):
    """
    Log in using phone number and receive a verification code.
    """

    SuccessResponseSchema = openapi.Schema(
        type="object",
        properties={
            "phone": openapi.Schema(type="string"),
            "code": openapi.Schema(type="string")
        }
    )
    FailedResponseSchema = openapi.Schema(
        type="object",
        properties={
            "message": openapi.Schema(type="string")
        }
    )

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type="object",
            properties={
                "phone": openapi.Schema(type="string", description="Phone number"),
            },
            required=["phone"],
        ),
        responses={
            200: openapi.Response(description="Successful response", schema=SuccessResponseSchema),
            400: openapi.Response(description="Bad Request", schema=FailedResponseSchema),
        },
    )
    def post(self, request):
        input_phone = request.data.get("phone")
        phone = "".join(filter(str.isdigit, input_phone))
        if len(phone) != 11:
            return Response(
                {"message": "Phone number must have exactly 11 digits."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        code = str(random.randint(1, 9999)).zfill(4)
        data = {
            "phone": phone,
            "code": code
        }
        time.sleep(2)
        return Response(data, status=status.HTTP_200_OK)

class VerifyView(APIView):
    """
    Verify the phone number using the received code.
    """

    SuccessResponseSchema = openapi.Schema(
        type="object",
        properties={
            "message": openapi.Schema(type="string"),
            "token": openapi.Schema(type="string")
        }
    )
    FailedResponseSchema = openapi.Schema(
        type="object",
        properties={
            "message": openapi.Schema(type="string")
        }
    )

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type="object",
            properties={
                "phone": openapi.Schema(type="string", description="Phone number"),
                "code": openapi.Schema(type="string", description="SMS code"),
                "verify": openapi.Schema(type="string", description="Verification code"),
            },
            required=["phone", "code", "verify"],
        ),
        responses={
            200: openapi.Response(description="Successful response", schema=SuccessResponseSchema),
            201: openapi.Response(description="Successful response", schema=SuccessResponseSchema),
            400: openapi.Response(description="Bad Request", schema=FailedResponseSchema),
        },
    )
    def post(self, request):
        input_phone = request.data.get("phone")
        phone_num = "".join(filter(str.isdigit, input_phone))
        code = request.data.get("code")
        verify = request.data.get("verify")
        if len(phone_num) != 11 or code != verify:
            error = "Invalid code."
            return Response(
                {"message": error},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            current_user = User.objects.get(username=phone_num)
            token, _ = Token.objects.get_or_create(user=current_user)
            return Response(
                {"message": "Login successful.", "token": token.key},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            current_user = User(username=phone_num)
            current_user.save()
            token = Token.objects.create(user=current_user)
            return Response(
                {"message": "User created and logged in.", "token": token.key},
                status=status.HTTP_201_CREATED
            )

class DataView(APIView):
    """
    View and manage user data.
    """
    permission_classes = [IsAuthenticated]

    SuccessGetResponseSchema = openapi.Schema(
        type="object",
        properties={
            "users": openapi.Schema(type="array", items=openapi.Schema(type="string")),
            "ref": openapi.Schema(type="string"),
            "invited": openapi.Schema(type="string")
        }
    )
    FailedGetResponseSchema = openapi.Schema(
        type="object",
        properties={
            "message": openapi.Schema(type="string")
        }
    )

    @swagger_auto_schema(
        responses={
            200: openapi.Response(description="Successful response", schema=SuccessGetResponseSchema),
            404: openapi.Response(description="Not Found", schema=FailedGetResponseSchema),
        },
    )
    def get(self, request):
        user = request.user
        try:
            user_instance = get_object_or_404(User, username=user.username)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        invited_value = user_instance.invited
        ref_value = user_instance.ref
        invited_users = User.objects.filter(invited=ref_value)
        invited_data = [i.username for i in invited_users]
        data = {
            "users": invited_data,
            "ref": ref_value,
            "invited": invited_value
        }
        return Response(data, status=status.HTTP_200_OK)

    SuccessResponseSchema = openapi.Schema(
        type="object",
        properties={
            "message": openapi.Schema(type="string"),
            "invited": openapi.Schema(type="string")
        }
    )
    FailedResponseSchema = openapi.Schema(
        type="object",
        properties={
            "message": openapi.Schema(type="string")
        }
    )

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type="object",
            properties={
                "ref_code": openapi.Schema(type="string", description="Referral code"),
            },
            required=["ref_code"],
        ),
        responses={
            200: openapi.Response(description="Successful response", schema=SuccessResponseSchema),
            400: openapi.Response(description="Bad Request", schema=FailedGetResponseSchema),
            404: openapi.Response(description="Not Found", schema=FailedGetResponseSchema),
        },
    )
    def post(self, request):
        user = request.user
        ref_code = request.data.get("ref_code")
        if not ref_code:
            return Response(
                {"message": "Referral code is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user_instance = User.objects.get(username=user.username)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        if user_instance.invited != "":
            return Response(
                {"message": "You cannot modify a registered referral code."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            ref_check = User.objects.get(ref=ref_code)
        except User.DoesNotExist:
            return Response(
                {"message": "No such code exists."},
                status=status.HTTP_404_NOT_FOUND
            )
        if ref_code == user_instance.ref:
            return Response(
                {"message": "You cannot invite yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user_instance.invited = ref_code
        user_instance.save()
        data = {
            "message": f"Referral code {ref_code} successfully registered.",
            "invited": ref_code,
        }
        return Response(data, status=status.HTTP_200_OK)
    
