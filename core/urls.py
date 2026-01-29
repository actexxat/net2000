from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from manager import views as manager_views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# Force a clean URL registry
urlpatterns = [
    # Auth
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='app_logout'),
    
    # Manager Actions
    path('toggle-served/<int:order_id>/', manager_views.toggle_served, name='serve_order_toggle'),
    path('discard-order/<int:order_id>/', manager_views.discard_order, name='discard_order'),
    path('restore-order/', manager_views.restore_order, name='restore_order'),
    path('serve-all-orders/<int:table_id>/', manager_views.serve_all_orders, name='serve_all_orders'),
    path('', manager_views.dashboard, name='dashboard'),
    path('dashboard/grid/', manager_views.dashboard_grid, name='dashboard_grid'),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    
    # Table Management
    path('checkin/<int:table_id>/', manager_views.check_in, name='check_in'),
    path('table/<int:table_id>/add_order/', manager_views.add_order, name='add_order'),
    path('table/<int:table_id>/add_order_direct/', manager_views.add_order_direct, name='add_order_direct'),
    path('table/<int:table_id>/checkout/', manager_views.check_out, name='check_out'),
    path('table/<int:table_id>/dismiss/', manager_views.dismiss_table, name='dismiss_table'),
    path('update-people/<int:table_id>/', manager_views.update_people, name='update_people'),
    path('refresh-table/<int:table_id>/', manager_views.refresh_table, name='refresh_table'),
    path('create-table/', manager_views.create_table, name='create_table'), 
    
    # Services
    path('add-print/<int:table_id>/', manager_views.add_print, name='add_print'),
    path('add-fax/<int:table_id>/', manager_views.add_fax, name='add_fax'),
    path('add-copy/<int:table_id>/', manager_views.add_copy, name='add_copy'),
    path('add-custom/<int:table_id>/', manager_views.add_custom_item, name='add_custom_item'),
    path('checkout-preview/<int:table_id>/', manager_views.checkout_preview, name='checkout_preview'),
    path('service-modal-preview/<int:table_id>/<str:service_type>/', manager_views.service_modal_preview, name='service_modal_preview'),
    path('item-popup/<int:table_id>/', manager_views.item_popup_preview, name='item_popup_preview'),
    
    # Sticky Notes
    path('sticky-note/add/', manager_views.add_sticky_note, name='add_sticky_note'),
    path('sticky-note/<int:note_id>/update/', manager_views.update_sticky_note, name='update_sticky_note'),
    path('sticky-note/<int:note_id>/delete/', manager_views.delete_sticky_note, name='delete_sticky_note'),
    
    # History & Stats
    path('history/', manager_views.session_history, name='session_history'),
    path('clear-data/', manager_views.clear_data, name='clear_data'),
    path('metrics/', manager_views.metrics_dashboard, name='metrics'),
    path('monitor/', manager_views.monitor, name='monitor'),
    path('unauthorized/', manager_views.unauthorized, name='unauthorized'),
    path('history/day/<int:year>/<int:month>/<int:day>/', manager_views.daily_receipt, name='daily_receipt'),
    path('history/revenue-30/', manager_views.revenue_30, name='revenue_30'),
    path('history/busy-times/', manager_views.busy_times, name='busy_times'),
    path('notification-history/', manager_views.notification_history, name='notification_history'), # Notification center endpoint
    
    # Menu
    path('menu/', include('manager.urls_menu')), 
]

if settings.DEBUG or getattr(settings, 'IS_FROZEN', False):
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]