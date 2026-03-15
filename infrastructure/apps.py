from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class InfrastructureConfig(AppConfig):
    name = 'infrastructure'
    verbose_name = _("Infrastructure")
