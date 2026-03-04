from core import version
from infrastructure.models import GlobalSettings

def version_info(request):
    """Provides version information and settings to all templates."""
    settings, _ = GlobalSettings.objects.get_or_create(id=1)
    return {
        'APP_VERSION': version.__version__,
        'BUILD_DATE': version.__build_date__,
        'GLOBAL_SETTINGS': settings,
    }
