from django.db import models
from django.contrib.auth.models import User

class CongaUser(models.Model):
    """Represents a single user in the system"""
    user = models.OneToOneField(User)
    mac = models.CharField(max_length=20)
    host = models.CharField(max_length=100)

    def __unicode__(self):
        return self.user.__unicode__()

class Conga(models.Model):
    """Represents a single conga"""
    name = models.CharField(max_length=80)
    password = models.CharField(max_length=80)
    owner = models.ForeignKey(User)

    class Meta(object):
        unique_together = ["name"]

    def __unicode__(self):
        return self.name

class CongaMember(models.Model):
    """Represents a member of the conga"""
    conga = models.ForeignKey(Conga)
    member = models.ForeignKey(User)
    index = models.IntegerField()

    def __unicode__(self):
        return self.conga.__unicode__() + ":" + self.member.__unicode__()


class Message(models.Model):
    """Represents a message being transferred around a conga"""
    message = models.CharField(max_length=1024)
    conga = models.ForeignKey(Conga)

    def __unicode__(self):
        return self.message

