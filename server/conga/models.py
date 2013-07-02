from django.db import models
from django.contrib.auth.models import User

class CongaUser(models.Model):
    """Represents a single user in the system"""
    user = models.OneToOneField(User)
    mac = models.CharField(max_length=20)
    host = models.CharField(max_length=20)

class Conga(models.Model):
    """Represents a single conga"""
    name = models.CharField(max_length=80)
    password = models.CharField(max_length=80)
    owner = models.ForeignKey(User)

class CongaMember(models.Model):
    """Represents a member of the conga"""
    conga = models.ForeignKey(Conga)
    member = models.ForeignKey(User)
    previous = models.IntegerField()

class Message(models.Model):
    """Represents a message being transferred around a conga"""
    message = models.CharField(max_length=1024)
    conga = models.ForeignKey(Conga)
