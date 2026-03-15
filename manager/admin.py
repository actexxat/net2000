from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from .models import Table, Item, Order, TableSession, QuickFireItem, QuickMenuItem, ActionLog
from unfold.admin import ModelAdmin
from unfold.forms import UserChangeForm, UserCreationForm, AdminPasswordChangeForm
from unfold.decorators import display, action
from django.utils.translation import gettext_lazy as _
from django import forms
from django.core.validators import RegexValidator


# ── Change-Username Form ─────────────────────────────────────────────────────

_username_validator = RegexValidator(
    r'^[\w.@+-]+$',
    _('150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
)


class ChangeUsernameForm(forms.Form):
    username = forms.CharField(
        label=_('New Username'),
        max_length=150,
        validators=[_username_validator],
        widget=forms.TextInput(attrs={'autofocus': True}),
    )
    username_confirm = forms.CharField(
        label=_('Confirm New Username'),
        max_length=150,
    )

    def __init__(self, *args, target_user=None, **kwargs):
        self.target_user = target_user
        super().__init__(*args, **kwargs)

    def clean_username(self):
        new = self.cleaned_data['username'].strip()
        if not new:
            raise forms.ValidationError(_('Username cannot be blank.'))
        # Case-insensitive uniqueness check, excluding the current user
        qs = User.objects.filter(username__iexact=new)
        if self.target_user:
            qs = qs.exclude(pk=self.target_user.pk)
        if qs.exists():
            raise forms.ValidationError(_('A user with that username already exists.'))
        return new

    def clean(self):
        cleaned = super().clean()
        u1 = cleaned.get('username', '').strip()
        u2 = cleaned.get('username_confirm', '').strip()
        if u1 and u2 and u1 != u2:
            raise forms.ValidationError(_("The two username fields didn't match."))
        return cleaned


# ── Model Admins ─────────────────────────────────────────────────────────────

@admin.register(Table)
class TableAdmin(ModelAdmin):
    list_display = ('number', 'capacity', 'status_badge', 'current_people')
    list_filter = ('is_occupied',)
    search_fields = ('number',)
    list_editable = ('capacity',)
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        (_('Configuration'), {
            'fields': ('number', 'capacity'),
        }),
        (_('Live State'), {
            'fields': ('is_occupied', 'current_people', 'opened_at', 'pending_reset'),
        }),
    )

    @display(description=_('Status'), label={
        True: 'danger',
        False: 'success',
    })
    def status_badge(self, obj):
        return _('Occupied') if obj.is_occupied else _('Available')


@admin.register(Item)
class ItemAdmin(ModelAdmin):
    list_display = ('name', 'price', 'category_badge', 'drink_badge')
    list_filter = ('category', 'is_drink')
    search_fields = ('name',)
    list_editable = ('price',)
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'price', 'category', 'is_drink'),
        }),
        (_('Media'), {
            'fields': ('image',),
        }),
    )

    @display(description=_('Category'), label=True)
    def category_badge(self, obj):
        return obj.category or _('Uncategorized'), 'info'

    @display(description=_('Type'), label={
        True: 'info',
        False: 'warning',
    })
    def drink_badge(self, obj):
        return _('Drink') if obj.is_drink else _('Other')


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('item_display', 'table', 'price_display', 'paid_status', 'timestamp_display', 'source_badge')
    list_filter = ('is_paid', 'order_source', 'shift', 'timestamp')
    search_fields = ('description', 'table__number', 'item__name')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'paid_at')
    autocomplete_fields = ('table', 'item')
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        (_('Selection'), {
            'fields': ('table', 'item'),
        }),
        (_('Transaction Details'), {
            'fields': ('transaction_price', 'is_paid', 'paid_at'),
        }),
        (_('Context'), {
            'fields': ('description', 'order_source', 'shift', 'timestamp', 'is_served'),
        }),
    )

    @display(description=_('Item'))
    def item_display(self, obj):
        return obj.item_name_display

    @display(description=_('Price'))
    def price_display(self, obj):
        p = obj.transaction_price if obj.transaction_price is not None else (obj.item.price if obj.item else 0)
        return f"{p:.2f} {str(_('EGP'))}"

    @display(description=_('Paid'), label={
        True: 'success',
        False: 'danger',
    })
    def paid_status(self, obj):
        return _('Paid') if obj.is_paid else _('Unpaid')

    @display(description=_('Source'), label=True)
    def source_badge(self, obj):
        return obj.get_order_source_display(), 'info'

    @display(description=_('Time'))
    def timestamp_display(self, obj):
        return obj.timestamp.strftime('%H:%M')


@admin.register(TableSession)
class TableSessionAdmin(ModelAdmin):
    list_display = ('table_number', 'checkout_time_display', 'total_amount_display', 'user', 'people_count', 'shift_badge')
    list_filter = ('checkout_time', 'user', 'shift', 'table_number')
    search_fields = ('items_summary', 'table_number')
    date_hierarchy = 'checkout_time'
    readonly_fields = ('checkout_time', 'session_start_time')
    compressed_fields = True

    fieldsets = (
        (_('Session Overview'), {
            'fields': ('table_number', 'people_count', 'total_amount', 'shift', 'user'),
        }),
        (_('Timestamps'), {
            'fields': ('session_start_time', 'checkout_time'),
        }),
        (_('Order Summary'), {
            'classes': ['collapse'],
            'fields': ('items_summary',),
        }),
    )

    @display(description=_('Checkout'))
    def checkout_time_display(self, obj):
        return obj.checkout_time.strftime('%d/%m/%Y %H:%M') if obj.checkout_time else '-'

    @display(description=_('Total'))
    def total_amount_display(self, obj):
        return f"{obj.total_amount:.2f} {str(_('EGP'))}"

    @display(description=_('Shift'), label=True)
    def shift_badge(self, obj):
        return obj.get_shift_display(), 'info'


@admin.register(QuickFireItem)
class QuickFireItemAdmin(ModelAdmin):
    list_display = ('item', 'order')
    list_editable = ('order',)
    list_display_links = ('item',)
    ordering = ('order',)


@admin.register(QuickMenuItem)
class QuickMenuItemAdmin(ModelAdmin):
    list_display = ('item', 'order')
    list_editable = ('order',)
    list_display_links = ('item',)
    ordering = ('order',)
    compressed_fields = True
    warn_unsaved_form = True


@admin.register(ActionLog)
class ActionLogAdmin(ModelAdmin):
    list_display = ('user', 'action_type_badge', 'table', 'timestamp_display')
    list_filter = ('action_type', 'user', 'timestamp')
    search_fields = ('details', 'user__username', 'table__number')
    readonly_fields = ('timestamp',)
    compressed_fields = True

    fieldsets = (
        (_('Identity'), {
            'fields': ('user', 'table'),
        }),
        (_('Action'), {
            'fields': ('action_type', 'details'),
        }),
        (_('Timestamp'), {
            'fields': ('timestamp',),
        }),
    )

    @display(description=_('Action'), label=True)
    def action_type_badge(self, obj):
        return str(_(obj.action_type)), 'info'

    @display(description=_('Time'))
    def timestamp_display(self, obj):
        return obj.timestamp.strftime('%d/%m/%Y %H:%M')


# ── User Admin (with Change Username) ────────────────────────────────────────

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    # Both buttons appear on the user detail page
    actions_detail = ['change_password_custom', 'change_username_custom']

    # ── Detail action buttons ──────────────────────────────────────────────

    @action(description=_('Change Password'), icon='lock')
    def change_password_custom(self, request, object_id):
        from django.shortcuts import redirect
        return redirect('admin:auth_user_password_change', object_id)

    @action(description=_('Change Username'), icon='badge')
    def change_username_custom(self, request, object_id):
        from django.shortcuts import redirect
        return redirect('admin:auth_user_change_username', object_id)

    # ── Custom URL + view ──────────────────────────────────────────────────

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                '<id>/change-username/',
                self.admin_site.admin_view(self.change_username_view),
                name='auth_user_change_username',
            ),
        ]
        # Prepend so our path wins over catch-alls
        return custom + urls

    def change_username_view(self, request, id):
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        from django.template.response import TemplateResponse
        from django.core.exceptions import PermissionDenied

        user_obj = get_object_or_404(User, pk=id)

        # Only superusers may change usernames
        if not request.user.is_superuser:
            raise PermissionDenied

        if request.method == 'POST':
            form = ChangeUsernameForm(request.POST, target_user=user_obj)
            if form.is_valid():
                old_username = user_obj.username
                new_username = form.cleaned_data['username']
                user_obj.username = new_username
                user_obj.save(update_fields=['username'])
                messages.success(
                    request,
                    _('Username changed from "%(old)s" to "%(new)s" successfully.') % {
                        'old': old_username, 'new': new_username
                    },
                )
                return redirect('admin:auth_user_change', user_obj.pk)
        else:
            form = ChangeUsernameForm(target_user=user_obj)

        context = {
            **self.admin_site.each_context(request),
            'title': _('Change Username'),
            'user_obj': user_obj,
            'form': form,
            'opts': User._meta,
            'media': self.media,
        }
        return TemplateResponse(
            request,
            'admin/auth/user/change_username.html',
            context,
        )


# ── Group Admin ───────────────────────────────────────────────────────────────

admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
