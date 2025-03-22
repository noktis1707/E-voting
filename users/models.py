from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken

    
class User(AbstractUser):
    avatar = models.CharField(max_length=300, blank=True, null=True)
    full_name = models.CharField(max_length=300, blank=True, null=True)
    s_n = models.CharField(max_length=30, blank=True, null=True)
    born = models.DateField(blank=True, null=True)

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return{
            'refresh':str(refresh),
            'access':str(refresh.access_token)
        }


    class Meta:
        db_table = "auth_user" 