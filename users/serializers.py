# from rest_framework import serializers
# from django.contrib import auth
# from rest_framework.exceptions import AuthenticationFailed
# from django.contrib.auth import get_user_model

# User = get_user_model()

# class LoginSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(max_length=68, min_length=6,write_only=True)
#     username = serializers.CharField(max_length=255, min_length=3)
#     tokens = serializers.SerializerMethodField()
#     def get_tokens(self, obj):
#         user = User.objects.get(username=obj['username'])
#         return {
#             'refresh': user.tokens()['refresh'],
#             'access': user.tokens()['access']
#         }
#     class Meta:
#         model = User
#         fields = ['password','username','tokens']
#     def validate(self, attrs):
#         username = attrs.get('username','')
#         password = attrs.get('password','')
#         user = auth.authenticate(username=username,password=password)
#         if not user:
#             raise AuthenticationFailed('Invalid credentials, try again')
#         if not user.is_active:
#             raise AuthenticationFailed('Account disabled, contact admin')
#         return {
#             'username': user.username,
#             'is_staff': user.is_staff,
#             'tokens': user.tokens
#         }