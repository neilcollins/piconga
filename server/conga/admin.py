from django.contrib import admin
from conga.models import CongaUser, Conga, CongaMember, Message

class CongaUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'host', 'mac')
    search_fields = ['host', 'mac', 'user__username']
admin.site.register(CongaUser, CongaUserAdmin)

class CongaAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    search_fields = ['name', 'owner__username']
admin.site.register(Conga, CongaAdmin)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('message', 'conga')
    search_fields = ['message', 'conga__name']
admin.site.register(Message, MessageAdmin)

admin.site.register(CongaMember)

