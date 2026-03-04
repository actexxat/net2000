from django.contrib import admin
from .models import GlobalSettings
from unfold.admin import ModelAdmin

@admin.register(GlobalSettings)
class GlobalSettingsAdmin(ModelAdmin):
    list_display = ('min_charge_per_person', 'active_shift', 'auto_logout_minutes', 'auto_logout_target')
    list_editable = ('active_shift', 'auto_logout_minutes', 'auto_logout_target')
    
    def has_add_permission(self, request):
        return False if GlobalSettings.objects.exists() else True

    def has_delete_permission(self, request, obj=None):
        return False
