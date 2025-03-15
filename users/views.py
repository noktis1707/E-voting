from django.shortcuts import render
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated 

    
class LoginView(APIView):

    def post(self, request, *args, **kwargs):
        user = authenticate(username=request.POST.get('username'),
                            password=request.POST.get('password'))

        if user:
            login(request, user)
            return Response({'token': 'Вход успешен'})
        return Response({'error': 'Неверные данные'}, status=400)

