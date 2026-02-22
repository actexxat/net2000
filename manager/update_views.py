"""
Views for the auto-update system.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
import threading

try:
    from core.updater import UpdateChecker
    from core.version import get_version_info
    UPDATER_AVAILABLE = True
except ImportError:
    try:
        from updater import UpdateChecker
        from version import get_version_info
        UPDATER_AVAILABLE = True
    except ImportError:
        UPDATER_AVAILABLE = False


@staff_member_required
def update_check_view(request):
    """View to display update information."""
    if not UPDATER_AVAILABLE:
        return JsonResponse({'error': 'Updater or version information not available'}, status=400)
    
    try:
        checker = UpdateChecker()
        info = get_version_info()
        
        # Check for actual updates on GitHub
        update_info = checker.check_for_updates()
        
        # Ensure all required keys exist in the response
        return JsonResponse({
            'current_version': info.get('version', 'Unknown'),
            'version': info.get('version', 'Unknown'),
            'build_date': info.get('build_date', ''),
            'available': update_info.get('available', False),
            'latest_version': update_info.get('latest_version', info.get('version')),
            'download_url': update_info.get('download_url'),
            'release_notes': update_info.get('release_notes', ''),
            'is_critical': update_info.get('is_critical', False),
            'error': update_info.get('error')
        })
    except Exception as e:
        return JsonResponse({
            'error': f'System error: {str(e)}',
            'current_version': 'Unknown'
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def update_download_view(request):
    """Start downloading an update."""
    if not UPDATER_AVAILABLE:
        return JsonResponse({'error': 'Updater not available'}, status=400)
    
    download_url = request.POST.get('download_url')
    if not download_url:
        return JsonResponse({'error': 'No download URL provided'}, status=400)
    
    checker = UpdateChecker()
    
    # Store progress in session
    request.session['update_progress'] = 0
    
    def progress_callback(progress):
        request.session['update_progress'] = progress
        request.session.save()
    
    # Download in background thread
    def download_task():
        zip_path = checker.download_update(download_url, progress_callback)
        if zip_path:
            update_script = checker.install_update(zip_path)
            request.session['update_script'] = update_script
            request.session['update_ready'] = True
            request.session.save()
    
    thread = threading.Thread(target=download_task, daemon=True)
    thread.start()
    
    return JsonResponse({'status': 'downloading'})


@staff_member_required
def update_progress_view(request):
    """Get download progress."""
    progress = request.session.get('update_progress', 0)
    ready = request.session.get('update_ready', False)
    
    return JsonResponse({
        'progress': progress,
        'ready': ready
    })


@staff_member_required
@require_http_methods(["POST"])
def update_apply_view(request):
    """Apply the downloaded update and restart."""
    if not UPDATER_AVAILABLE:
        return JsonResponse({'error': 'Updater not available'}, status=400)
    
    update_script = request.session.get('update_script')
    if not update_script:
        return JsonResponse({'error': 'No update ready to apply'}, status=400)
    
    checker = UpdateChecker()
    checker.apply_update_and_restart(update_script)
    
    return JsonResponse({'status': 'restarting'})

@staff_member_required
def system_update_view(request):
    """Render the standalone System Update page."""
    return render(request, 'manager/system_update_full.html')
