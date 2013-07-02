from django.contrib import admin
from conga.models import CongaUser, Conga, CongaMember, Message

admin.site.register(CongaUser)
admin.site.register(Conga)
admin.site.register(CongaMember)
admin.site.register(Message)
