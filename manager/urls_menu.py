from django.urls import path
from . import views_menu

urlpatterns = [
    path('qr-codes/', views_menu.qr_dashboard, name='qr_dashboard'),
    path('<int:table_id>/', views_menu.public_menu, name='public_menu'),
    path('<int:table_id>/order/', views_menu.public_place_order, name='public_place_order'),
    path('<int:table_id>/submit-cart/', views_menu.public_submit_cart, name='public_submit_cart'),
    path('check-updates/', views_menu.check_dashboard_updates, name='check_dashboard_updates'),
    path('toggle-served/<int:order_id>/', views_menu.toggle_served_redirect, name='serve_order_toggle_menu'),
]
