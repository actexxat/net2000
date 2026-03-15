from django.db import models
from django.utils.translation import gettext_lazy as _

class GlobalSettings(models.Model):
    SHIFT_CHOICES = [('MORNING', _('Morning')), ('NIGHT', _('Night'))]
    min_charge_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=25.00, verbose_name=_("Min Charge Per Person"))
    active_shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, default='MORNING', verbose_name=_("Active Shift"))
    auto_logout_minutes = models.IntegerField(default=0, help_text=_("Wait minutes before automatic logout. Set to 0 to disable."), verbose_name=_("Auto Logout Minutes"))
    AUTO_LOGOUT_TARGETS = [
        ('ALL', _('All Users')),
        ('NON_ADMIN', _('Users except Admin')),
    ]
    auto_logout_target = models.CharField(
        max_length=10, 
        choices=AUTO_LOGOUT_TARGETS, 
        default='ALL',
        help_text=_("Select which users are subject to automatic logout."),
        verbose_name=_("Auto Logout Target")
    )
    last_global_logout = models.DateTimeField(null=True, blank=True, help_text=_("Timestamp of the last triggered global logout."), verbose_name=_("Last Global Logout"))
    last_global_logout_ip = models.GenericIPAddressField(null=True, blank=True, help_text=_("IP address that triggered the last global logout."), verbose_name=_("Last Global Logout IP"))

    def __str__(self):
        return str(_("Global Space Settings"))

    class Meta:
        app_label = 'infrastructure'
        verbose_name = _("Global Setting")
        verbose_name_plural = _("Global Settings")
        # Keep the old table name to avoid data loss
        db_table = 'manager_globalsettings'
