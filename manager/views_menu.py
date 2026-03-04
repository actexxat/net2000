from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _
import socket
from django.contrib.auth.decorators import login_required
from .models import Table, Item, Order
from infrastructure.models import GlobalSettings

def get_local_ip():
    """Get the local network IP address of the server."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@login_required
def qr_dashboard(request):
    """Admin view to list all tables and generate their QR codes."""
    tables = Table.objects.all().order_by('number')
    local_ip = get_local_ip()
    return render(request, 'menu/qr_dashboard.html', {
        'tables': tables,
        'local_ip': local_ip
    })

def public_menu(request, table_id):
    """Customer view: The Digital Menu."""
    table = get_object_or_404(Table, id=table_id)
    items = Item.objects.all().order_by('category', 'name')
    
    # 1. Collect all doubles
    doubles = {} # base_name -> double_item
    for it in items:
        if "(Double)" in it.name:
            base = it.name.replace("(Double)", "").strip().lower()
            doubles[base] = it
            
    # 2. Group items and attach doubles to singles
    grouped = {}
    for it in items:
        if 'Service' in it.name: continue
        
        # Skip standalone double entries as they will be merged into singles
        if "(Double)" in it.name:
            continue
            
        # Standardize name for display
        it.short_name = it.name.replace("(Single)", "").strip()
        
        # Check for double counterpart
        base = it.short_name.lower()
        it.double_variant = doubles.get(base)
        
        cat = getattr(it, 'category', 'Other') or 'Other'
        grouped.setdefault(cat, []).append(it)
        
    return render(request, 'menu/public_menu.html', {
        'table': table,
        'grouped_items': grouped,
    })

@require_POST
def public_place_order(request, table_id):
    """Handle order submission from the public menu."""
    table = get_object_or_404(Table, id=table_id)
    item_id = request.POST.get('item_id')
    
    try:
        item = Item.objects.get(id=item_id)
        # Create order
        # Mark as NOT paid
        Order.objects.create(table=table, item=item, is_paid=False, order_source='QR')
        
        # Determine if we should Auto-Checkin the table?
        # Yes, if it's not occupied, ordering something implies occupation.
        if not table.is_occupied:
            table.is_occupied = True
            from django.utils import timezone
            table.opened_at = timezone.now()
            table.save()
            
        messages.success(request, _("Ordered: %(item)s") % {'item': item.name})
    except Exception:
        messages.error(request, _("Failed to order."))
    
    return redirect('public_menu', table_id=table.id)

@require_POST
def public_submit_cart(request, table_id):
    """Handle bulk order submission from the cart."""
    import json
    from django.http import JsonResponse
    from django.utils import timezone

    table = get_object_or_404(Table, id=table_id)
    try:
        data = json.loads(request.body)
        items_data = data.get('items', [])
        
        if not items_data:
            return JsonResponse({'success': False, 'error': 'No items in cart'}, status=400)

        created_count = 0
        for item_data in items_data:
            item_id = item_data.get('id')
            quantity = int(item_data.get('quantity', 1))
            note = item_data.get('note', '')
            
            item = Item.objects.get(id=item_id)
            for _ in range(quantity):
                Order.objects.create(
                    table=table, 
                    item=item, 
                    is_paid=False, 
                    order_source='QR',
                    description=note if note else None
                )
                created_count += 1
        
        # Auto-Checkin logic
        if not table.is_occupied:
            table.is_occupied = True
            table.opened_at = timezone.now()
            table.save()
            
        return JsonResponse({'success': True, 'count': created_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def check_dashboard_updates(request):
    """Check if there are any changes to the dashboard (new orders)."""
    from django.http import JsonResponse
    from django.utils.dateparse import parse_datetime
    from django.utils import timezone
    
    last_check_str = request.GET.get('last_check')
    
    new_orders = []
    if last_check_str:
        last_check = parse_datetime(last_check_str)
        if last_check:
            # Get orders created AFTER the last check
            orders = Order.objects.filter(
                is_paid=False,
                timestamp__gt=last_check
            ).select_related('table', 'item').order_by('timestamp')
            
            for order in orders:
                table_name = order.table.number if order.table else "Unknown"
                
                # Use new property names
                name = order.item_name_display
                cat = order.item_category_display
                
                if cat:
                    item_display = f"({cat}) {name}"
                else:
                    item_display = name
                    
                new_orders.append({
                    'table': table_name,
                    'item': item_display,
                    'id': order.id,
                    'source': order.order_source
                })
    
    return JsonResponse({
        'has_updates': len(new_orders) > 0,
        'orders': new_orders,
        'timestamp': timezone.now().isoformat()
    })

@login_required
def toggle_served_redirect(request, order_id):
    """Toggles the is_served status of an order via HTMX. (Redirected route)"""
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        order.is_served = not order.is_served
        order.save()
        
        # We need _get_table_context which is in views.py
        # To avoid circular imports, we'll do the work here or import inside
        from .views import _get_table_context
        if order.table:
            _get_table_context(order.table)
            return render(request, 'manager/partials/table_card.html', {'table': order.table})
            
    return redirect('dashboard')

def heartbeat(request):
    """Simple endpoint to check if server is alive."""
    from django.http import HttpResponse
    return HttpResponse("OK", content_type="text/plain")
