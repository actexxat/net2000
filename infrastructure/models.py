from django.db import models

class GlobalSettings(models.Model):
    SHIFT_CHOICES = [('MORNING', 'Morning'), ('NIGHT', 'Night')]
    min_charge_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=25.00)
    active_shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, default='MORNING')
    auto_logout_minutes = models.IntegerField(default=0, help_text="Wait minutes before automatic logout. Set to 0 to disable.")
    AUTO_LOGOUT_TARGETS = [
        ('ALL', 'All Users'),
        ('NON_ADMIN', 'Users except Admin'),
    ]
    auto_logout_target = models.CharField(
        max_length=10, 
        choices=AUTO_LOGOUT_TARGETS, 
        default='ALL',
        help_text="Select which users are subject to automatic logout."
    )
    last_global_logout = models.DateTimeField(null=True, blank=True, help_text="Timestamp of the last triggered global logout.")
    last_global_logout_ip = models.GenericIPAddressField(null=True, blank=True, help_text="IP address that triggered the last global logout.")

    def __str__(self):
        return "Global Space Settings"

    class Meta:
        app_label = 'infrastructure'
        verbose_name_plural = "Global Settings"
        # Keep the old table name to avoid data loss
        db_table = 'manager_globalsettings'
