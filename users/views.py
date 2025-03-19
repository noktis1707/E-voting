from django.shortcuts import render
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from rest_framework.views import APIView


class LoginView(APIView):
    
    def post(self, request, *args, **kwargs):
        user = authenticate(username= request.data.get('username'),
                            password=request.data.get('password'))

        if user:
            login(request, user)
            return Response({'token': 'Вход успешен'})
        return Response({'error': 'Неверные данные'}, status=400)

