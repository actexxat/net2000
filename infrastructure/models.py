from django.db import models

class GlobalSettings(models.Model):
    SHIFT_CHOICES = [('MORNING', 'Morning'), ('NIGHT', 'Night')]
    min_charge_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=25.00)
    active_shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, default='MORNING')

    def __str__(self):
        return "Global Space Settings"

    class Meta:
        app_label = 'infrastructure'
        verbose_name_plural = "Global Settings"
        # Keep the old table name to avoid data loss
        db_table = 'manager_globalsettings'
