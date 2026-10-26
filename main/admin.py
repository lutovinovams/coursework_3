from django.contrib import admin
from main.models import Client, Message, Mailing, Log

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'comment')
    search_fields = ('full_name', 'email')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title', 'body')


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_time', 'end_time', 'status', 'message')
    list_filter = ('status', 'start_time')
    filter_horizontal = ('recipients',)


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('id', 'mailing', 'attempt_time', 'status', 'server_response')
    list_filter = ('status', 'attempt_time')
