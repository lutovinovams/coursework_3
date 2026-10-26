from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.forms import widgets
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from main.models import Client, Message, Mailing, Log
from main.services import send_mailing_messages


class ManagerAccessMixin:
    """Запрещает менеджерам редактировать/удалять чужие данные."""

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user.groups.filter(name='Manager').exists():
            raise PermissionDenied("Менеджеры не могут изменять или удалять данные.")
        if obj.owner != self.request.user:
            raise PermissionDenied("У вас нет прав на изменение этого объекта.")
        return obj


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'main/client_list.html'

    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager').exists():
            return super().get_queryset()
        return super().get_queryset().filter(owner=self.request.user)


class ClientDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Client
    template_name = 'main/client_detail.html'

    def test_func(self):
        obj = self.get_object()
        return self.request.user.groups.filter(name='Manager').exists() or obj.owner == self.request.user


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    fields = ['email', 'full_name', 'comment']
    success_url = reverse_lazy('main:client_list')
    template_name = 'main/client_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


class ClientUpdateView(LoginRequiredMixin, ManagerAccessMixin, UpdateView):
    model = Client
    fields = ['email', 'full_name', 'comment']
    success_url = reverse_lazy('main:client_list')
    template_name = 'main/client_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


class ClientDeleteView(LoginRequiredMixin, ManagerAccessMixin, DeleteView):
    model = Client
    success_url = reverse_lazy('main:client_list')
    template_name = 'main/client_confirm_delete.html'


class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'main/message_list.html'

    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager').exists():
            return super().get_queryset()
        return super().get_queryset().filter(owner=self.request.user)


class MessageDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Message
    template_name = 'main/message_detail.html'

    def test_func(self):
        obj = self.get_object()
        return self.request.user.groups.filter(name='Manager').exists() or obj.owner == self.request.user


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    fields = ['title', 'body']
    success_url = reverse_lazy('main:message_list')
    template_name = 'main/message_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


class MessageUpdateView(LoginRequiredMixin, ManagerAccessMixin, UpdateView):
    model = Message
    fields = ['title', 'body']
    success_url = reverse_lazy('main:message_list')
    template_name = 'main/message_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


class MessageDeleteView(LoginRequiredMixin, ManagerAccessMixin, DeleteView):
    model = Message
    success_url = reverse_lazy('main:message_list')
    template_name = 'main/message_confirm_delete.html'


class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = 'main/mailing_list.html'

    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager').exists():
            queryset = super().get_queryset()
        else:
            queryset = super().get_queryset().filter(owner=self.request.user)
        for mailing in queryset:
            mailing.update_status()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        user = self.request.user

        if user.groups.filter(name='Manager').exists():
            mailings_qs = Mailing.objects.all()
            logs_qs = Log.objects.all()
        else:
            mailings_qs = Mailing.objects.filter(owner=user)
            logs_qs = Log.objects.filter(mailing__owner=user)

        context['total_mailings'] = mailings_qs.count()
        context['active_mailings'] = mailings_qs.filter(
            start_time__lte=now, end_time__gte=now, status=Mailing.STATUS_STARTED, is_active=True
        ).count()
        context['total_unique_clients'] = Client.objects.count()

        context['success_logs_count'] = logs_qs.filter(status=Log.STATUS_SUCCESS).count()
        context['failed_logs_count'] = logs_qs.filter(status=Log.STATUS_FAILED).count()
        context['total_sent_messages'] = logs_qs.count()
        return context


class MailingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Mailing
    template_name = 'main/mailing_detail.html'

    def test_func(self):
        obj = self.get_object()
        return self.request.user.groups.filter(name='Manager').exists() or obj.owner == self.request.user

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logs'] = self.object.logs.all()
        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    fields = ['start_time', 'end_time', 'message', 'recipients']
    success_url = reverse_lazy('main:mailing_list')
    template_name = 'main/mailing_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['start_time'].widget = widgets.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'})
        form.fields['end_time'].widget = widgets.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'})
        form.fields['message'].widget.attrs.update({'class': 'form-select'})
        form.fields['recipients'].widget.attrs.update({'class': 'form-select', 'rows': '5'})
        return form


class MailingUpdateView(LoginRequiredMixin, ManagerAccessMixin, UpdateView):
    model = Mailing
    fields = ['start_time', 'end_time', 'message', 'recipients']
    success_url = reverse_lazy('main:mailing_list')
    template_name = 'main/mailing_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['start_time'].widget = widgets.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'})
        form.fields['end_time'].widget = widgets.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'})
        form.fields['message'].widget.attrs.update({'class': 'form-select'})
        form.fields['recipients'].widget.attrs.update({'class': 'form-select', 'rows': '5'})
        return form


class MailingDeleteView(LoginRequiredMixin, ManagerAccessMixin, DeleteView):
    model = Mailing
    success_url = reverse_lazy('main:mailing_list')
    template_name = 'main/mailing_confirm_delete.html'


class MailingActionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.groups.filter(name='Manager').exists():
            raise PermissionDenied("Менеджеры не могут запускать рассылки вручную.")
        mailing = get_object_or_404(Mailing, pk=pk, owner=request.user)
        success = send_mailing_messages(mailing)
        if success:
            messages.success(request, "Рассылка успешно запущена, сообщения отправляются.")
        else:
            messages.error(request,
                           "Ошибка инициации: текущее время вне интервала работы рассылки или рассылка заблокирована.")
        return redirect('main:mailing_detail', pk=pk)


class MailingToggleActiveView(LoginRequiredMixin, View):
    """Экшен-контроллер менеджера для включения/выключения рассылки."""

    def post(self, request, pk):
        if not request.user.groups.filter(name='Manager').exists():
            raise PermissionDenied("Только менеджеры могут изменять статус активности.")
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.is_active = not mailing.is_active
        mailing.status = Mailing.STATUS_CREATED if not mailing.is_active else mailing.status
        mailing.save()
        messages.success(request, f"Статус активности рассылки #{pk} успешно изменен.")
        return redirect('main:mailing_detail', pk=pk)
