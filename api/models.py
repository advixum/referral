import random, string
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver


# Create your models here.

class User(AbstractUser):
    username = models.CharField('Телефон', max_length=11, unique=True)
    ref = models.CharField('Реферал', max_length=6, unique=True)
    invited = models.CharField('Приглашён', max_length=6, default="")

@receiver(pre_save, sender=User)
def gen_ref(sender, instance, **kwargs):
    if not instance.ref:
        while True:
            ref = ''.join(
                random.choices(string.ascii_letters + string.digits, k=6)
            )
            if not User.objects.filter(ref=ref).exists():
                instance.ref = ref
                break
