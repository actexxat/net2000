from core import version

def version_info(request):
    """Provides version information to all templates."""
    return {
        'APP_VERSION': version.__version__,
        'BUILD_DATE': version.__build_date__,
    }
