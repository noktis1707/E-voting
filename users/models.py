from django.db import models
from django.contrib.auth.models import AbstractUser

    
# class User(AbstractUser):
#     full_name = models.CharField(max_length=300, blank=True, null=True)
#     s_n = models.CharField(max_length=30, blank=True, null=True)
#     born = models.DateField()

#     class Meta:
#         db_table = "auth_user" 