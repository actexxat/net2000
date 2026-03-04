"""
Middleware for enforcing version requirements and update checks.
"""

from django.shortcuts import render
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.auth import logout
from infrastructure.models import GlobalSettings

try:
    try:
        from core.version import is_version_allowed, get_version_info
    except ImportError:
        from version import is_version_allowed, get_version_info
    VERSION_CHECK_AVAILABLE = True
except ImportError:
    VERSION_CHECK_AVAILABLE = False


class VersionEnforcementMiddleware(MiddlewareMixin):
    """
    Middleware that blocks access if the application version is below the minimum required.
    This allows you to force users to update by setting __minimum_required_version__ in version.py
    """
    
    # Paths that are always allowed (to enable update functionality)
    ALLOWED_PATHS = [
        '/system-update/',
        '/update/',
        '/static/',
        '/media/',
        '/login/',
        '/admin/',
    ]
    
    def process_request(self, request):
        """Check version before processing any request."""
        
        if not VERSION_CHECK_AVAILABLE:
            return None
        
        # Allow certain paths even if version is outdated
        for allowed_path in self.ALLOWED_PATHS:
            if request.path.startswith(allowed_path):
                return None
        
        # Check if version is allowed locally
        allowed, message = is_version_allowed()
        version_info = get_version_info()
        
        # Check GitHub for updates (cached)
        from django.core.cache import cache
        github_update = cache.get('github_update_info')
        if github_update is None:
            try:
                from core.updater import check_for_updates_simple
                github_update = check_for_updates_simple()
                cache.set('github_update_info', github_update, 3600) # Cache for 1 hour
            except Exception:
                github_update = {'available': False}
                cache.set('github_update_info', github_update, 300) # Cache error for 5 mins
                
        if github_update and github_update.get('available'):
            allowed = False
            new_version = github_update.get('latest_version', 'Unknown')
            message = f"A required system update (v{new_version}) is available. The system has been paused. Admin must install this update to continue."

        if not allowed:
            # Return a blocking page that forces update
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Update Required</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        background: white;
                        border-radius: 16px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        padding: 40px;
                        max-width: 500px;
                        text-align: center;
                    }}
                    .icon {{
                        font-size: 64px;
                        margin-bottom: 20px;
                    }}
                    h1 {{
                        color: #333;
                        margin: 0 0 10px 0;
                        font-size: 28px;
                    }}
                    .version {{
                        color: #666;
                        font-size: 14px;
                        margin-bottom: 20px;
                    }}
                    .message {{
                        color: #e74c3c;
                        background: #fee;
                        padding: 15px;
                        border-radius: 8px;
                        margin: 20px 0;
                        border-left: 4px solid #e74c3c;
                    }}
                    .btn {{
                        display: inline-block;
                        background: #667eea;
                        color: white;
                        padding: 12px 30px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: 600;
                        transition: all 0.3s;
                        border: none;
                        cursor: pointer;
                        font-size: 16px;
                    }}
                    .btn:hover {{
                        background: #5568d3;
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                    }}
                    .info {{
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #eee;
                        color: #999;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">🔒</div>
                    <h1>Update Required</h1>
                    <div class="version">Current Version: {version_info['version']}</div>
                    <div class="message">
                        {message}
                    </div>
                    <a href="/system-update/" class="btn">Go to Update Page</a>
                    <div class="info">
                        This application requires an update to continue.<br>
                        Please proceed to the update page to install the latest version.
                    </div>
                </div>
            </body>
            </html>
            """
            
            return HttpResponse(html, status=403)
        
        return None


class AutoLogoutMiddleware(MiddlewareMixin):
    """
    Middleware that automatically logs out users after a period of inactivity.
    Also handles global logout signaled from other devices on the same network.
    """
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def process_request(self, request):
        # Skip for non-authenticated users
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
            
        # Skip for static and media files to avoid unnecessary DB hits
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None

        # Get settings
        try:
            settings, _ = GlobalSettings.objects.get_or_create(id=1)
            now = timezone.now()
            client_ip = self.get_client_ip(request)

            # --- 1. Global Logout Check ---
            # Skip if user is excluded based on management settings (e.g. Admin shouldn't be affected if target is NON_ADMIN)
            is_excluded = (settings.auto_logout_target == 'NON_ADMIN' and request.user.is_superuser)
            
            if not is_excluded:
                login_time_str = request.session.get('login_timestamp')
                if login_time_str:
                    try:
                        login_time = timezone.datetime.fromisoformat(login_time_str)
                        if timezone.is_naive(login_time):
                            login_time = timezone.make_aware(login_time)
                        
                        if settings.last_global_logout and settings.last_global_logout > login_time:
                            logout(request)
                            return None
                    except (ValueError, TypeError):
                        request.session['login_timestamp'] = now.isoformat()
                else:
                    request.session['login_timestamp'] = now.isoformat()

            # --- 2. Idle Logout Check ---
            if settings.auto_logout_minutes <= 0:
                if 'last_activity' in request.session:
                    del request.session['last_activity']
                return None

            if settings.auto_logout_target == 'NON_ADMIN' and request.user.is_superuser:
                return None

            last_activity_str = request.session.get('last_activity')

            if last_activity_str:
                try:
                    last_activity = timezone.datetime.fromisoformat(last_activity_str)
                    if timezone.is_naive(last_activity):
                        last_activity = timezone.make_aware(last_activity)
                        
                    idle_duration = (now - last_activity).total_seconds() / 60

                    if idle_duration > settings.auto_logout_minutes:
                        # Signal Global Logout for this network
                        settings.last_global_logout = now
                        settings.last_global_logout_ip = client_ip
                        settings.save(update_fields=['last_global_logout', 'last_global_logout_ip'])
                        
                        logout(request)
                        return None
                except (ValueError, TypeError):
                    pass

            request.session['last_activity'] = now.isoformat()
            
        except Exception:
            pass
            
        return None
