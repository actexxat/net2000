from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import models
from django.db.models import Sum, Q, Prefetch, Avg, Count, Max, Min, F, ExpressionWrapper, fields
from django.db.models.functions import Coalesce, ExtractHour, ExtractWeekDay
from .models import Table, Item, Order, TableSession, GlobalSettings
from decimal import Decimal
import datetime, json
from django.utils.translation import gettext_lazy as _, get_language
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied

def superuser_required(view_func):
    """Decorator for views that checks that the user is a superuser, redirecting to unauthorized if not."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser:
            # print(f"ACCESS DENIED: User {request.user.username} is not a superuser.")
            return redirect('unauthorized')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
def unauthorized(request):
    """Returns a nice-looking access denied page."""
    return render(request, 'manager/unauthorized.html')

def _get_table_context(table, settings=None):
    """
    Internal helper to calculate table totals and attach them to the object.
    Optimized to use prefetched 'active_orders' if available.
    """
    if not settings:
        settings, created = GlobalSettings.objects.get_or_create(id=1)
    
    if table.is_occupied:
        # Use prefetched orders if available, otherwise query DB
        if hasattr(table, 'active_orders'):
            unpaid_orders = table.active_orders
            # Mock filtered queryset behavior for consistency if needed in templates, 
            # though usually list is fine for iteration.
            # But we need to support .filter() calls if templates use them?
            # Templates usually just iterate {{ table.orders }}.
        else:
            unpaid_orders = list(table.order_set.filter(is_paid=False).select_related('item').order_by('timestamp'))
        
        # Calculate totals in Python to avoid DB hits
        order_total = Decimal('0.00')
        drinks = []
        
        for order in unpaid_orders:
            real_price = order.transaction_price if order.transaction_price is not None else (order.item.price if order.item else Decimal('0.00'))
            order_total += real_price or 0
            
            is_drink = order.item.is_drink if order.item else False
            if is_drink:
                drinks.append(real_price or Decimal('0.00'))
        
        # Sort drinks descending to give user the best coverage
        drinks.sort(reverse=True)
        
        shortfall = Decimal('0.00')
        if int(table.number) != 0:
            min_charge = settings.min_charge_per_person
            for i in range(table.current_people):
                if i < len(drinks):
                    shortfall += max(Decimal('0.00'), min_charge - drinks[i])
                else:
                    shortfall += min_charge
        else:
            shortfall = Decimal('0.00')
        
        # Attach variables
        table.actual_orders = order_total
        table.shortfall = shortfall
        table.final_total = order_total + shortfall
        table.orders = unpaid_orders
        
        # Calculate Progress
        if int(table.number) != 0 and table.current_people > 0:
            total_target = table.current_people * settings.min_charge_per_person
            if total_target > 0:
                covered = total_target - shortfall
                table.min_charge_progress = int((covered / total_target) * 100)
            else:
                table.min_charge_progress = 100
        else:
            table.min_charge_progress = 100
    else:
        table.actual_orders = 0
        table.shortfall = 0
        table.final_total = 0
        table.min_charge_progress = 0
    return table

def _get_sorted_tables(sort_by_status=True):
    """Helper to get all tables sorted by status, with contexts prepared."""
    from django.db.models import Prefetch
    from .models import Table, Order, GlobalSettings, Item
    
    # Ensure Table 0 exists and is always occupied
    t0, created = Table.objects.get_or_create(number=0, defaults={'capacity': 50, 'is_occupied': True})
    if not t0.is_occupied:
        t0.is_occupied = True
        t0.save()
    
    all_tables = Table.objects.all().prefetch_related(
        Prefetch('order_set', 
                 queryset=Order.objects.filter(is_paid=False).select_related('item').order_by('timestamp'), 
                 to_attr='active_orders')
    )
    
    # Custom sorting: Table 0 always first, then occupied (asc), then empty (asc)
    table_0 = [t for t in all_tables if t.number == 0]
    others = [t for t in all_tables if t.number != 0]
    
    if sort_by_status:
        occupied = sorted([t for t in others if t.is_occupied], key=lambda x: x.number)
        empty = sorted([t for t in others if not t.is_occupied], key=lambda x: x.number)
        tables = table_0 + occupied + empty
    else:
        # Stable sort by number for polling updates to prevent reordering
        others_sorted = sorted(others, key=lambda x: x.number)
        tables = table_0 + others_sorted

    settings, _ = GlobalSettings.objects.get_or_create(id=1)
    for table in tables:
        _get_table_context(table, settings)
        
    return tables

@login_required
def dashboard(request):
    """Main view to see all tables and their current bills."""
    from django.db.models import Prefetch
    
    tables = _get_sorted_tables()
    
    settings, _ = GlobalSettings.objects.get_or_create(id=1)
    
    # Items grouping logic...
    
    items = Item.objects.all()
    # Group items by category if available, otherwise use simple heuristics
    # 1. Collect all doubles
    doubles = {} # base_name -> double_item
    for it in items:
        if "(Double)" in it.name:
            base = it.name.replace("(Double)", "").strip().lower()
            doubles[base] = it

    # 2. Group items and attach doubles to singles
    grouped = {}
    for it in items:
        if "(Double)" in it.name:
            continue
            
        # Standardize name for display
        # Remove (Single) case-insensitive and strip
        temp_name = it.name.replace("(Single)", "").replace("(single)", "").strip()
        it.short_name = temp_name
        
        # Check for double counterpart with EXACT base matching
        base = temp_name.lower()
        it.double_variant = doubles.get(base)
        
        # If no double found, try stripped versions as fallback (e.g. extra spaces)
        if not it.double_variant:
             base_stripped = base.strip()
             if base_stripped in doubles:
                 it.double_variant = doubles[base_stripped]

        # prefer explicit attribute `category` if present
        cat = getattr(it, 'category', None)
        if not cat:
            name = (it.name or '').lower()
            if 'hot' in name:
                cat = 'Hot'
            elif 'cold' in name:
                cat = 'Cold'
            elif 'juice' in name:
                cat = 'Juice'
            elif 'tea' in name or 'coffee' in name:
                cat = 'Hot'
            else:
                cat = 'Other'
        grouped.setdefault(cat, []).append(it)
    # sort categories and items
    grouped_items = {k: sorted(v, key=lambda x: x.name) for k, v in sorted(grouped.items())}
    
    # Get the global minimum charge (creates a default of 25 if none exists)
    # Quick Fire Items (Top 5 selling)
    # Quick Fire Items (Specific User Request)
    target_names = ["turkish coffee", "tea", "water", "latte", "redbull", "twist", "v cola", "sun top", "volt"]
    quick_items = []
    
    # 1. Fetch prefered items in order
    for name_query in target_names:
        # fuzzy match or exact match logic
        found = next((i for i in items if name_query in i.name.lower()), None)
        if found and found not in quick_items:
            quick_items.append(found)

    # 2. Fill remainder with top sellers if needed (up to 12 items for bar)
    if len(quick_items) < 12:
        top_ids = Order.objects.filter(item__isnull=False).values('item').annotate(c=Count('id')).order_by('-c')[:12]
        for t in top_ids:
            try:
                candidate = Item.objects.get(id=t['item'])
                if candidate not in quick_items:
                    quick_items.append(candidate)
            except Item.DoesNotExist:
                continue
    
    # Limit to reasonable number
    quick_items = quick_items[:12]

    return render(request, 'manager/dashboard.html', {
        'tables': tables,
        'items': items,
        'grouped_items': grouped_items,
        'quick_items': quick_items,
        'global_min_charge': settings.min_charge_per_person,
        'server_now': timezone.now().isoformat()
    })

@login_required
def dashboard_grid(request):
    """Returns OOB updates for all tables to update them in-place."""
    import hashlib
    from django.http import HttpResponse, HttpResponseNotModified
    from django.template.loader import render_to_string
    from django.db.models import Max, Count, Sum
    
    # 1. Cheap State Check (DB Aggregation) to avoid rendering
    # We want to catch: New Orders, Deleted Orders, Served Status Change, People Count Change, Table Status Change
    
    orders_agg = Order.objects.filter(is_paid=False).aggregate(
        cnt=Count('id'), 
        max_id=Max('id'), 
        served_cnt=Sum('is_served')
    )
    
    tables_agg = Table.objects.aggregate(
        occupied_cnt=Count('id', filter=models.Q(is_occupied=True)),
        people_sum=Sum('current_people')
    )
    
    # Create a unique state string
    # We add a 'version' salt (v2) to ensure template changes invalidate the cache
    state_str = f"{orders_agg['cnt']}-{orders_agg['max_id']}-{orders_agg['served_cnt']}-{tables_agg['occupied_cnt']}-{tables_agg['people_sum']}-v2"
    
    # Explicitly check if 'last_updated' session variable (if we used one) matches? 
    # Or just hash this state.
    et = hashlib.md5(state_str.encode('utf-8')).hexdigest()
    
    # Handle quoted ETags
    client_etag = request.headers.get('If-None-Match', '')
    if client_etag.startswith('W/'):
        client_etag = client_etag[2:]
    client_etag = client_etag.strip('"')
    
    if client_etag == et:
        return HttpResponseNotModified()

    # 2. Fetch Data & Render (Only if changed)
    tables = _get_sorted_tables(sort_by_status=True)
    content = render_to_string('manager/partials/table_grid.html', {'tables': tables}, request=request)
    
    response = HttpResponse(content)
    response['ETag'] = f'"{et}"'
    return response

@login_required
def notification_history(request):
    """Returns a partial list of recent QR orders."""
    # filtering for QR orders
    qr_orders = Order.objects.filter(order_source='QR').order_by('-timestamp')[:20].select_related('table', 'item')
    return render(request, 'manager/partials/notification_history.html', {'orders': qr_orders})

@login_required
def check_in(request, table_id):
    """Marks a table as occupied. Accepts people_count from POST if provided."""
    if request.method == "POST":
        table = get_object_or_404(Table, id=table_id)
        
        # Security: Clear any ghost orders that might exist on this 'closed' table
        # This prevents the "newly opened table has orders" confusion
        table.order_set.filter(is_paid=False).delete()
        
        table.is_occupied = True
        table.opened_at = timezone.now()
        try:
            table.current_people = int(request.POST.get('people_count', 1))
        except ValueError:
            table.current_people = 1
        table.save()
        messages.success(request, _("Table %(number)s checked in.") % {'number': table.number})
        
        if request.headers.get('HX-Request'):
            # Return full grid to re-sort
            tables = _get_sorted_tables()
            # print(f"DEBUG: check_in returning {len(tables)} tables") 
            return render(request, 'manager/partials/table_grid.html', {'tables': tables})
            
    return redirect('dashboard')

@login_required
def refresh_table(request, table_id):
    """Returns a single table card for targeted UI updates."""
    table = get_object_or_404(Table, id=table_id)
    _get_table_context(table)
    return render(request, 'manager/partials/table_card.html', {'table': table})

@login_required
def update_people(request, table_id):
    """Updates the number of people at a table from the card input."""
    if request.method == "POST":
        table = get_object_or_404(Table, id=table_id)
        table.current_people = int(request.POST.get('people_count', 1))
        table.save()
        messages.success(request, _("Updated people for Table %(number)s.") % {'number': table.number})
        
        if request.headers.get('HX-Request'):
            _get_table_context(table)
            return render(request, 'manager/partials/table_card.html', {'table': table})
            
    return redirect('dashboard')

@login_required
def add_order(request, table_id):
    """
    GET: Returns the Add Order modal with the menu.
    POST: Adds selected items to the table's bill (Legacy cart support).
    """
    table = get_object_or_404(Table, id=table_id)

    if request.method == "GET":
        # logic to populate menu items for the modal
        items = Item.objects.all()
        doubles = {} 
        for it in items:
            if "(Double)" in it.name:
                base = it.name.replace("(Double)", "").strip().lower()
                doubles[base] = it

        grouped = {}
        for it in items:
            if "(Double)" in it.name:
                continue
            
            temp_name = it.name.replace("(Single)", "").replace("(single)", "").strip()
            it.short_name = temp_name
            
            base = temp_name.lower()
            it.double_variant = doubles.get(base)
            if not it.double_variant:
                 base_stripped = base.strip()
                 if base_stripped in doubles:
                     it.double_variant = doubles[base_stripped]

            cat = getattr(it, 'category', None)
            if not cat:
                name = (it.name or '').lower()
                if 'hot' in name:
                    cat = 'Hot'
                elif 'cold' in name:
                    cat = 'Cold'
                elif 'juice' in name:
                    cat = 'Juice'
                elif 'tea' in name or 'coffee' in name:
                    cat = 'Hot'
                else:
                    cat = 'Other'
            grouped.setdefault(cat, []).append(it)
        
        grouped_items = {k: sorted(v, key=lambda x: x.name) for k, v in sorted(grouped.items())}
         
        return render(request, 'manager/partials/modals/order_modal.html', {
            'table': table,
            'grouped_items': grouped_items
        })

    if request.method == "POST":
        # Handle list of item_ids (cart) and fallback to single item_id
        item_ids = request.POST.getlist('item_ids')
        if not item_ids:
            single_id = request.POST.get('item_id')
            if single_id:
                item_ids = [single_id]
        
        added_items = []
        for item_id in item_ids:
            try:
                item = Item.objects.get(id=item_id)
                Order.objects.create(
                    table=table, 
                    item=item, 
                    transaction_price=item.price,
                    order_source='DIRECT'
                )
                added_items.append(item.name)
            except (Item.DoesNotExist, ValueError):
                continue
        
        if added_items:
            if len(added_items) == 1:
                messages.success(request, _("Added %(item)s to Table %(number)s.") % {'item': added_items[0], 'number': table.number})
            else:
                messages.success(request, _("Added %(count)s items to Table %(number)s.") % {'count': len(added_items), 'number': table.number})
        else:
            messages.error(request, _("Failed to add items to bill."))
            
        if request.headers.get('HX-Request'):
            _get_table_context(table)
            return render(request, 'manager/partials/table_card.html', {'table': table})
            
    return redirect('dashboard')

@login_required
def check_out(request, table_id):
    """Calculates final total, saves to history, and resets the table."""
    table = get_object_or_404(Table, id=table_id)
    settings = GlobalSettings.objects.get(id=1)
    
    unpaid_orders = table.order_set.filter(is_paid=False)
    
    order_total = Decimal('0.00')
    drinks = []
    items_list = []
    
    for order in unpaid_orders:
        price = order.transaction_price if order.transaction_price is not None else (order.item.price if order.item else Decimal('0.00'))
        price = price or Decimal('0.00')
        order_total += price
        
        name = order.item_name_display
        note = order.customer_note_display
        if note:
            items_list.append(f"{name} [{note}]")
        else:
            items_list.append(name)
        
        is_drink = order.item.is_drink if order.item else False
        if is_drink:
            drinks.append(price)

    items_summary = ", ".join(items_list) if items_list else "No items ordered"
    
    # Sort drinks descending
    drinks.sort(reverse=True)
    
    shortfall = Decimal('0.00')
    if int(table.number) != 0:
        min_charge = settings.min_charge_per_person
        for i in range(table.current_people):
            if i < len(drinks):
                shortfall += max(Decimal('0.00'), min_charge - drinks[i])
            else:
                shortfall += min_charge
    else:
        shortfall = Decimal('0.00')
            
    final_bill = order_total + shortfall

    # 1. Save record to history
    TableSession.objects.create(
        table_number=table.number,
        people_count=table.current_people,
        items_summary=items_summary,
        total_amount=final_bill,
        check_in_time=table.opened_at or timezone.now(),
        user=request.user
    )

    # 2. Reset the table and mark orders as paid
    unpaid_orders.update(is_paid=True)
    
    # Table 0 is a special permanent table (e.g. for takeaway)
    if int(table.number) != 0:
        table.is_occupied = False
        table.current_people = 0
    else:
        table.is_occupied = True
        table.current_people = 1 # Keep at least 1 person for context
        table.opened_at = timezone.now() # Reset opening time
        
    table.save()
    messages.success(request, _("Checked out Table %(number)s. Recorded EGP %(bill).2f") % {'number': table.number, 'bill': final_bill})
    
    if request.headers.get('HX-Request'):
        _get_table_context(table)
        return render(request, 'manager/partials/table_card.html', {'table': table})
        
    return redirect('dashboard')

@superuser_required
def metrics_dashboard(request):
    """Business Intelligence dashboard with advanced metrics and insights."""
    if not request.user.is_superuser:
        return redirect('unauthorized')
    from django.db.models import Sum, Count, Avg, Min, Max, F, ExpressionWrapper, fields
    from django.db.models.functions import ExtractHour, ExtractWeekDay, Coalesce
    import datetime
    
    is_ar = get_language() == 'ar'
    def _loc(val):
        if not is_ar: return str(val)
        return str(val).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))

    now = timezone.localtime(timezone.now())
    today = now.date()
    
    # 1. Comparison & Growth
    last_week_day = today - datetime.timedelta(days=7)
    today_sessions = TableSession.objects.filter(check_out_time__date=today)
    last_week_sessions = TableSession.objects.filter(check_out_time__date=last_week_day)
    
    today_rev = today_sessions.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    last_week_rev = last_week_sessions.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    
    growth = 0
    if last_week_rev > 0:
        growth = ((today_rev - last_week_rev) / last_week_rev) * 100
    
    # 2. Product Performance
    paid_item_orders = Order.objects.filter(is_paid=True).exclude(item=None)
    top_selling_items = paid_item_orders.values('item__name').annotate(
        count=Count('id'),
        revenue=Sum(Coalesce('transaction_price', 'item__price'))
    ).order_by('-count')[:5]

    category_data = paid_item_orders.values('item__category').annotate(
        revenue=Sum(Coalesce('transaction_price', 'item__price'))
    ).order_by('-revenue')

    # 3. Efficiency Metrics
    all_sessions = TableSession.objects.all()
    avg_duration = all_sessions.annotate(
        duration=ExpressionWrapper(F('check_out_time') - F('check_in_time'), output_field=fields.DurationField())
    ).aggregate(Avg('duration'))['duration__avg']
    
    if avg_duration:
        total_secs = avg_duration.total_seconds()
        hours = int(total_secs // 3600)
        minutes = int((total_secs % 3600) // 60)
        avg_dur_str = f"{_loc(hours)}{_('h')} {_loc(minutes)}{_('m')}" if hours > 0 else f"{_loc(minutes)}{_('m')}"
    else:
        avg_dur_str = f"0{_('m')}"

    total_rev_all = all_sessions.aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')
    total_people_all = all_sessions.aggregate(s=Sum('people_count'))['s'] or 1
    avg_bill = all_sessions.aggregate(a=Avg('total_amount'))['a'] or 0
    avg_per_person = total_rev_all / total_people_all

    table_count = Table.objects.count() or 1
    recent_sessions = all_sessions.filter(check_out_time__date__gte=today - datetime.timedelta(days=6))
    total_active_duration = recent_sessions.annotate(
        duration=ExpressionWrapper(F('check_out_time') - F('check_in_time'), output_field=fields.DurationField())
    ).aggregate(s=Sum('duration'))['s']
    
    occupancy_rate = 0
    if total_active_duration:
        total_possible_secs = table_count * 12 * 3600 * 7 # 12h workday
        occupancy_rate = (total_active_duration.total_seconds() / total_possible_secs) * 100

    # 4. Audit & Security
    opening_time = today_sessions.aggregate(m=Min('check_in_time'))['m']
    closing_time = today_sessions.aggregate(m=Max('check_out_time'))['m']

    # 5. Existing Metrics
    total_count = all_sessions.count()
    import re
    regex_bw = re.compile(r'B/W.*?\((\d+)\s*pages\)', re.IGNORECASE)
    regex_color = re.compile(r'Color.*?\((\d+)\s*pages\)', re.IGNORECASE)
    
    today_printing = Order.objects.filter(item__name="Printing Service", timestamp__date=today).values('description')
    today_bw = sum(int(regex_bw.search(po['description'] or "").group(1)) for po in today_printing if regex_bw.search(po['description'] or ""))
    today_color = sum(int(regex_color.search(po['description'] or "").group(1)) for po in today_printing if regex_color.search(po['description'] or ""))

    # Top Tables
    table_rev_agg = all_sessions.values('table_number').annotate(revenue=Sum('total_amount'), count=Count('id')).order_by('-revenue')[:5]
    top_tables = [{'number': _loc(tr['table_number']), 'revenue': _loc(f"{tr['revenue']:.2f}"), 'count': _loc(tr['count'])} for tr in table_rev_agg]

    # Hourly Heatmap
    hourly_traffic = all_sessions.annotate(h=ExtractHour('check_out_time')).values('h').annotate(c=Count('id'), r=Sum('total_amount')).order_by('h')
    hours_labels = [f"{h:02d}:00" for h in range(24)]
    hours_data_rev = [0.0] * 24
    for h in hourly_traffic:
        hours_data_rev[h['h']] = float(h['r'] or 0)

    # Traffic Prediction
    django_day_map = {1: 2, 2: 3, 4: 5, 5: 6, 6: 7, 7: 1, 3: 4} # Corrected dict
    current_django_day = django_day_map[now.isoweekday()]
    limit_date = today - datetime.timedelta(days=90)
    h_history = all_sessions.filter(check_out_time__date__gte=limit_date).annotate(wd=ExtractWeekDay('check_out_time'), h=ExtractHour('check_out_time')).filter(wd=current_django_day)
    h_map = {x['h']: x['c'] for x in h_history.values('h').annotate(c=Count('id'))}
    peak_count = max(h_map.values()) if h_map else 1
    
    def get_pred_score(hr_range):
        avg = sum(h_map.get((now.hour + i) % 24, 0) for i in range(1, hr_range + 1)) / hr_range
        return max(1, min(10, round((avg / peak_count) * 10)))

    pred_3h = get_pred_score(3)
    future_h = sorted([ (h, c) for h, c in h_map.items() if h > now.hour ], key=lambda x: x[1], reverse=True)[:3]
    future_h.sort(key=lambda x: x[0])
    rush_str = ", ".join([f"{(x[0] % 12) or 12} {_('AM') if x[0] < 12 else _('PM')}" for x in future_h]) if future_h else _("No more for today")

    return render(request, 'manager/metrics.html', {
        'total_count': _loc(total_count),
        'today_rev': _loc(f"{today_rev:.2f}"),
        'growth': round(growth, 1),
        'top_items': top_selling_items,
        'category_data': category_data,
        'avg_duration': avg_dur_str,
        'avg_bill': _loc(f"{avg_bill:.2f}"),
        'avg_per_person': _loc(f"{avg_per_person:.2f}"),
        'occupancy': round(occupancy_rate, 1),
        'opening_time': timezone.localtime(opening_time).strftime('%H:%M') if opening_time else "--:--",
        'closing_time': timezone.localtime(closing_time).strftime('%H:%M') if closing_time else "--:--",
        'today_bw': _loc(today_bw),
        'today_color': _loc(today_color),
        'top_tables': top_tables,
        'pred_3h': _loc(pred_3h),
        'rush_hours': _loc(rush_str),
        'hours_labels': json.dumps(hours_labels),
        'hours_data_rev': json.dumps(hours_data_rev),
        'is_ar': is_ar,
    })

@superuser_required
def session_history(request):
    """Displays past transactions filtered by a specific date."""
    if not request.user.is_superuser:
        return redirect('unauthorized')
        
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
             selected_date = timezone.localtime(timezone.now()).date()
    else:
        selected_date = timezone.localtime(timezone.now()).date()

    # Robust Range Filtering: 
    # specific __date lookups can sometimes be flaky depending on DB driver/OS timezones.
    # explicit range is safer.
    start_local = datetime.datetime.combine(selected_date, datetime.time.min)
    end_local = datetime.datetime.combine(selected_date, datetime.time.max)
    
    # Ensure timezone awareness
    current_tz = timezone.get_current_timezone()
    start_aware = timezone.make_aware(start_local, current_tz)
    end_aware = timezone.make_aware(end_local, current_tz)

    sessions = TableSession.objects.filter(check_out_time__range=(start_aware, end_aware)).order_by('-check_out_time')
    
    is_ar = get_language() == 'ar'
    def _loc(val):
        if not is_ar: return str(val)
        return str(val).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))
        
    loc_sessions = []
    for s in sessions:
        loc_sessions.append({
            'obj': s,
            'table_number_loc': _loc(s.table_number),
            'p_count_loc': _loc(s.people_count),
            'total_loc': _loc(f"{s.total_amount:.2f}"),
            'time_loc': _loc(timezone.localtime(s.check_out_time).strftime('%H:%M'))
        })
        
    return render(request, 'manager/history.html', {
        'sessions': loc_sessions,
        'selected_date': selected_date,
        'total_count': _loc(sessions.count()),
    })

def create_table(request):
    """Quickly create a new table from the dashboard modal."""
    if request.method == "POST":
        number = request.POST.get('table_number')
        capacity = request.POST.get('capacity')
        try:
            Table.objects.create(number=number, capacity=capacity)
            messages.success(request, _("Created Table %(number)s.") % {'number': number})
        except Exception:
            messages.error(request, _("Failed to create table."))
    return redirect('dashboard')


@login_required
def add_print(request, table_id):
    """Handle manual print orders (B/W or Color). Uses generic 'Printing Service' item."""
    if request.method == "POST":
        table = get_object_or_404(Table, id=table_id)
        try:
            pages = int(request.POST.get('pages', 0))
        except Exception:
            pages = 0
        ptype = request.POST.get('print_type', 'bw')

        if ptype == 'bw':
            # per-page pricing: <=100 pages -> 1.00 EGP per page, >100 -> 0.75 EGP per page
            if pages <= 100:
                ppp = Decimal('1.00')
            else:
                ppp = Decimal('0.75')
            total = (Decimal(pages) * ppp).quantize(Decimal('0.01'))
            name = _("Printing B/W (%(pages)s pages)") % {'pages': pages}
        else:
            # color: accept manual total cost entry
            try:
                total = Decimal(request.POST.get('color_cost', '0')).quantize(Decimal('0.01'))
            except Exception:
                total = Decimal('0.00')
            name = _("Printing Color (%(pages)s pages)") % {'pages': pages}

        # Use generic Item. MUST exist (created by admin).
        try:
            item = Item.objects.get(name="Printing Service")
        except Item.DoesNotExist:
            messages.error(request, _("Error: 'Printing Service' item not found. Please contact Admin."))
            return redirect('dashboard')

        try:
            Order.objects.create(
                table=table, 
                item=item,
                transaction_price=total,
                description=name
            )
            messages.success(request, _("Added %(name)s to Table %(number)s.") % {'name': name, 'number': table.number})
        except Exception:
            messages.error(request, _("Failed to add print to bill."))
            
        if request.headers.get('HX-Request'):
            _get_table_context(table)
            return render(request, 'manager/partials/table_card.html', {'table': table})
            
    return redirect('dashboard')


@superuser_required
def revenue_30(request):
    """Return revenue totals for each of the last 30 days."""
    if not request.user.is_superuser:
        return redirect('unauthorized')
    today = datetime.date.today()
    dates = []
    totals = []

    from django.db.models import Sum

    for i in range(29, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_total = TableSession.objects.filter(check_out_time__date=day).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        dates.append(day.strftime('%Y-%m-%d'))
        totals.append(float(day_total))

    return render(request, 'manager/revenue_chart.html', {
        'dates_json': json.dumps(dates),
        'totals_json': json.dumps(totals),
    })

@superuser_required
def busy_times(request):
    """Analyze busy and slow times based on past sessions (Hour of day & Day of week)."""
    if not request.user.is_superuser:
        return redirect('unauthorized')
    from django.db.models import Count
    from django.db.models.functions import ExtractHour, ExtractWeekDay

    sessions = TableSession.objects.all()

    # 1. Hourly Traffic (0-23)
    hourly = sessions.annotate(h=ExtractHour('check_out_time')).values('h').annotate(c=Count('id')).order_by('h')
    h_map = {x['h']: x['c'] for x in hourly}
    
    hours_labels = [f"{h:02d}:00" for h in range(24)]
    hours_data = [h_map.get(h, 0) for h in range(24)]

    # 2. Daily Traffic (1=Sunday ... 7=Saturday)
    daily = sessions.annotate(d=ExtractWeekDay('check_out_time')).values('d').annotate(c=Count('id')).order_by('d')
    d_map = {x['d']: x['c'] for x in daily}

    # Sort Mon(2) -> Sun(1)
    week_order = [2, 3, 4, 5, 6, 7, 1]
    day_names = {1:'Sun', 2:'Mon', 3:'Tue', 4:'Wed', 5:'Thu', 6:'Fri', 7:'Sat'}
    
    days_labels = [day_names[d] for d in week_order]
    days_data = [d_map.get(d, 0) for d in week_order]

    return render(request, 'manager/busy_times.html', {
        'hours_labels': json.dumps(hours_labels),
        'hours_data': json.dumps(hours_data),
        'days_labels': json.dumps(days_labels),
        'days_data': json.dumps(days_data),
    })

@superuser_required
def monitor(request):
    """Monitoring screen: summary of currently occupied tables, people, orders and totals."""
    if not request.user.is_superuser:
        return redirect('unauthorized')
    # Use Prefetch to avoid N+1 queries for orders and their items
    unpaid_orders_prefetch = Prefetch(
        'order_set',
        queryset=Order.objects.filter(is_paid=False).select_related('item').order_by('timestamp'),
        to_attr='active_orders'
    )
    tables = Table.objects.filter(is_occupied=True).prefetch_related(unpaid_orders_prefetch).order_by('number')
    all_tables = Table.objects.all().order_by('number')
    settings, created = GlobalSettings.objects.get_or_create(id=1)

    busy_tables = []
    total_people = 0
    total_due = Decimal('0.00')

    for table in tables:
        order_total = Decimal('0.00')
        drinks = []
        orders = []
        
        for o in table.active_orders:
            price = o.transaction_price if o.transaction_price is not None else (o.item.price if o.item else Decimal('0.00'))
            price = price or Decimal('0.00')
            order_total += price
            
            orders.append({
                'name': o.item_name_display,
                'category': o.item_category_display,
                'note': o.customer_note_display,
                'price': price
            })
            
            is_drink = o.item.is_drink if o.item else False
            if is_drink:
                drinks.append(price)

        # Sort drinks descending
        drinks.sort(reverse=True)
        
        shortfall = Decimal('0.00')
        if int(table.number) != 0:
            min_charge = settings.min_charge_per_person
            for i in range(table.current_people):
                if i < len(drinks):
                    shortfall += max(Decimal('0.00'), min_charge - drinks[i])
                else:
                    shortfall += min_charge
        else:
            shortfall = Decimal('0.00')
        
        final_total = order_total + shortfall

        busy_tables.append({
            'id': table.id,
            'number': table.number,
            'people': table.current_people,
            'orders': orders,
            'order_total': order_total,
            'shortfall': shortfall,
            'final_total': final_total,
        })

        total_people += table.current_people
        total_due += final_total

    context = {
        'busy_count': len(busy_tables),
        'busy_tables': busy_tables,
        'total_people': total_people,
        'total_due': total_due,
        'all_tables': all_tables,
    }
    return render(request, 'manager/monitor.html', context)

@require_POST
@login_required
def add_order_direct(request, table_id):
    """
    Instantly adds a single item to the table order via HTMX.
    Returns:
       1. The updated table card (OOB swap)
       2. A toast notification (OOB swap)
       3. The updated 'Live' order list for the modal (OOB swap)
    """
    from django.utils.translation import gettext as _
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    from decimal import Decimal, InvalidOperation
    table = get_object_or_404(Table, id=table_id)
    
    item_id = request.POST.get('item_id')
    price_val = request.POST.get('price')
    
    try:
        item = Item.objects.get(id=item_id)
    except (Item.DoesNotExist, ValueError):
        return HttpResponse("Error: Item not found", status=400)
        
    try:
        price = Decimal(price_val)
    except (ValueError, TypeError, InvalidOperation):
        price = item.price
        
    # Create the order
    order = Order.objects.create(
        table=table,
        item=item,
        is_paid=False,
        transaction_price=price,
        order_source='WalkIn'
    )
    
    # Refresh table context for the card update
    settings, created = GlobalSettings.objects.get_or_create(id=1)
    _get_table_context(table, settings)
    
    # Render the updated table card
    card_html = render_to_string('manager/partials/table_card.html', {
        'table': table, 
        'is_oob': True,
        'suppress_messages': True
    }, request=request)
    
    # Render the toast notification
    toast_html = render_to_string('manager/partials/toast_notification.html', {
        'message': _("Added %(item)s to Table %(number)s") % {'item': item.name, 'number': table.number},
        'level': 'success'
    }, request=request)
    
    # Render the updated 'Live List' for the ongoing modal session
    # We neeed active orders for this specific table
    active_orders = table.order_set.filter(is_paid=False).select_related('item').order_by('-timestamp')
    live_list_html = render_to_string('manager/partials/live_order_list.html', {
        'orders': active_orders,
        'table': table
    }, request=request)
    
    # Render a small OOB update for the badge count in the modal
    from manager.templatetags.manager_extras import translate_numbers
    count_loc = translate_numbers(active_orders.count())
    badge_html = f'<span class="badge bg-danger rounded-pill" id="live-order-badge" hx-swap-oob="true">{count_loc}</span>'
    
    return HttpResponse(card_html + toast_html + live_list_html + badge_html)


@require_POST
@login_required
def add_fax(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    pages = int(request.POST.get('pages', 1))
    
    try:
        price = Decimal(request.POST.get('cost', 0))
    except (ValueError, TypeError, InvalidOperation):
        price = Decimal(pages * 5)
    
    try:
        fax_item = Item.objects.get(name="Fax Service")
    except Item.DoesNotExist:
        messages.error(request, _("Error: 'Fax Service' item not found. Please contact Admin."))
        return redirect('dashboard')
    
    desc_str = _("Fax Service (%(pages)s pages)") % {'pages': pages}
    Order.objects.create(
        table=table,
        item=fax_item,
        is_paid=False,
        description=desc_str,
        transaction_price=price
    )
    
    messages.success(request, _("Added Fax (%(pages)s pages) to Table %(number)s. Cost: %(cost)s") % {
        'pages': pages, 
        'number': table.number,
        'cost': price
    })
    
    if request.headers.get('HX-Request'):
        _get_table_context(table)
        return render(request, 'manager/partials/table_card.html', {'table': table})
        
    return redirect('dashboard')


@require_POST
@login_required
def add_copy(request, table_id):
    """Handle manual copy orders with user-defined cost."""
    table = get_object_or_404(Table, id=table_id)
    
    try:
        pages = int(request.POST.get('pages', 0))
    except (ValueError, TypeError):
        pages = 0
        
    ctype = request.POST.get('copy_type', 'bw')

    if ctype == 'bw':
        # Tiered pricing: <=100 pages -> 1.00 EGP, >100 pages -> 0.75 EGP
        if pages <= 100:
            ppp = Decimal('1.00')
        else:
            ppp = Decimal('0.75')
        total = (Decimal(pages) * ppp).quantize(Decimal('0.01'))
        type_str = _("B/W")
    else:
        # Color: manual cost input
        try:
            total = Decimal(request.POST.get('color_cost', 0))
        except (ValueError, TypeError, InvalidOperation):
            total = Decimal('0.00')
        type_str = _("Color")
    
    name = _("Copy (%(type)s) (%(pages)s pages)") % {'type': type_str, 'pages': pages}

    try:
        item = Item.objects.get(name="Copy Service")
    except Item.DoesNotExist:
        messages.error(request, _("Error: 'Copy Service' item not found. Please contact Admin."))
        return redirect('dashboard')

    try:
        Order.objects.create(
            table=table, 
            item=item,
            transaction_price=total,
            description=name,
            is_paid=False
        )
        messages.success(request, _("Added %(name)s to Table %(number)s. Cost: %(cost)s") % {
            'name': name, 
            'number': table.number,
            'cost': total
        })
    except Exception:
        messages.error(request, _("Failed to add copy to bill."))
        
    if request.headers.get('HX-Request'):
        _get_table_context(table)
        return render(request, 'manager/partials/table_card.html', {'table': table})
        
    return redirect('dashboard')

@login_required
def service_modal_preview(request, table_id, service_type):
    """Returns the dynamic content for a specific service modal."""
    table = get_object_or_404(Table, id=table_id)
    
    # Common categories for order modal
    items = Item.objects.all()
    # 1. Collect all doubles
    doubles = {} # base_name -> double_item
    for it in items:
        if "(Double)" in it.name:
            base = it.name.replace("(Double)", "").strip().lower()
            doubles[base] = it

    # 2. Group items and attach doubles to singles
    grouped = {}
    for it in items:
        # Skip service items if desired, or keep them. 
        # The prompt implies standardizing drinks, so filtering 'Service' might be safe or required depending on data.
        # Ideally we shouldn't filter generic services out unless intended, but the menu view does.
        # We will follow the menu view's lead but be careful about 'Service' items if they are used here.
        # Actually, 'Printing Service' etc are manual items, usually not in this list or filtered differently?
        # The menu view filters `if 'Service' in it.name: continue`. 
        # The dashboard usually includes everything. I will keep everything but handle doubles.
        
        if "(Double)" in it.name:
            continue
            
        # Standardize name for display
        # Remove (Single) case-insensitive and strip
        temp_name = it.name.replace("(Single)", "").replace("(single)", "").strip()
        it.short_name = temp_name
        
        # Check for double counterpart
        base = temp_name.lower()
        it.double_variant = doubles.get(base)
        
        # If no double found, try stripped versions as fallback
        if not it.double_variant:
             base_stripped = base.strip()
             if base_stripped in doubles:
                 it.double_variant = doubles[base_stripped]
        
        cat = getattr(it, 'category', None)
        if not cat:
            name = (it.name or '').lower()
            if 'hot' in name: cat = 'Hot'
            elif 'cold' in name: cat = 'Cold'
            elif 'juice' in name: cat = 'Juice'
            elif 'tea' in name or 'coffee' in name: cat = 'Hot'
            else: cat = 'Other'
        grouped.setdefault(cat, []).append(it)
    grouped_items = {k: sorted(v, key=lambda x: x.name) for k, v in sorted(grouped.items())}

    template_map = {
        'order': 'manager/partials/modals/order_modal.html',
        'print': 'manager/partials/modals/print_modal.html',
        'fax': 'manager/partials/modals/fax_modal.html',
        'copy': 'manager/partials/modals/copy_modal.html',
        'custom': 'manager/partials/modals/custom_modal.html',
    }
    
    template_name = template_map.get(service_type)
    if not template_name:
        return HttpResponseBadRequest("Invalid service type")

    return render(request, template_name, {
        'table': table,
        'grouped_items': grouped_items,
    })


@require_POST
@login_required
def add_custom_item(request, table_id):
    """Handle custom manual items with user-defined name and price."""
    table = get_object_or_404(Table, id=table_id)
    
    item_name = request.POST.get('item_name', '').strip()
    if not item_name:
        item_name = _("Custom Service")
        
    try:
        price = Decimal(request.POST.get('price', 0))
    except (ValueError, TypeError, InvalidOperation):
        price = Decimal('0.00')

    # Use no item (Custom)
    item = None

    try:
        Order.objects.create(
            table=table, 
            item=item,
            transaction_price=price,
            description=item_name,
            is_paid=False
        )
        messages.success(request, _("Added '%(name)s' to Table %(number)s. Price: %(price)s") % {
            'name': item_name, 
            'number': table.number,
            'price': price
        })
    except Exception:
        messages.error(request, _("Failed to add custom item to bill."))
        
    if request.headers.get('HX-Request'):
        _get_table_context(table)
        return render(request, 'manager/partials/table_card.html', {'table': table})
        
    return redirect('dashboard')


@login_required
def checkout_preview(request, table_id):
    """
    Returns the partial HTML for the checkout modal with dynamic totals.
    """
    table = get_object_or_404(Table, id=table_id)
    global_settings = GlobalSettings.objects.first()
    
    # Calculate totals using the same logic as checkout
    # _get_table_context returns the table object with attached attributes
    ctx = _get_table_context(table, global_settings)
    
    # Pass all context variables needed for the modal
    context = {
        'table': table,
        'actual_orders_list': ctx.orders,  # attribute is .orders
        'total_orders_price': ctx.actual_orders, # attribute is .actual_orders
        'shortfall': ctx.shortfall,
        'final_total': ctx.final_total,
    }
    return render(request, 'manager/partials/checkout_modal_content.html', context)

@login_required
def toggle_served(request, order_id):
    """Toggles the is_served status of an order via HTMX."""
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        order.is_served = not order.is_served
        order.save()
        
        # Return the updated table card to refresh the UI
        if order.table:
            _get_table_context(order.table)
            return render(request, 'manager/partials/table_card.html', {'table': order.table})
            
    return redirect('dashboard')

@login_required
def discard_order(request, order_id):
    """Deletes an order from a table."""
    if request.method == "POST":
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        
        order = get_object_or_404(Order, id=order_id)
        table = order.table
        item_name = order.item_name_display
        
        # Save for Undo
        request.session['deleted_order'] = {
            'item_id': order.item.id if order.item else None,
            'description': order.description,
            'price': str(order.transaction_price) if order.transaction_price else '0.00',
            'table_id': table.id,
            'order_type': order.order_source
        }
        
        order.delete()
        
        if table:
            _get_table_context(table)
            
            if request.headers.get('HX-Request'):
                # 1. Update Table Card
                card_html = render_to_string('manager/partials/table_card.html', {
                    'table': table,
                    'is_oob': True,
                    'suppress_messages': True
                }, request=request)
                
                # 2. Update Live List
                active_orders = table.order_set.filter(is_paid=False).select_related('item').order_by('-timestamp')
                live_list_html = render_to_string('manager/partials/live_order_list.html', {
                    'orders': active_orders,
                    'table': table
                }, request=request)
                
                # 3. Badge Update
                from manager.templatetags.manager_extras import translate_numbers
                count_loc = translate_numbers(active_orders.count())
                badge_html = f'<span class="badge bg-danger rounded-pill" id="live-order-badge" hx-swap-oob="true">{count_loc}</span>'
                
                # 4. Toast Notification with UNDO
                # We construct a toast message that includes a clickable Undo action
                undo_url = request.build_absolute_uri('/restores-latest/') # Need to register this
                msg = _("Removed %(item)s") % {'item': item_name}
                # Create a small interactive HTML button for the toast
                action_html = f"""
                <button class='btn btn-sm btn-light ms-2 py-0 fw-bold' 
                        hx-post='/restore-order/' 
                        hx-swap='none'
                        onclick='this.closest(".message-popup").remove()'>
                    { _('UNDO') }
                </button>
                """
                
                toast_html = render_to_string('manager/partials/toast_notification.html', {
                    'message': f"{msg} {action_html}",
                    'level': 'dark', # Dark toast for contrast
                    'safe_mode': True # Tell template to render HTML
                }, request=request)
                
                return HttpResponse(card_html + live_list_html + badge_html + toast_html)
            
            # Fallback for non-HTMX
            messages.success(request, _("Item removed: %(item)s") % {'item': item_name})
            return render(request, 'manager/partials/table_card.html', {'table': table})
            
    return redirect('dashboard')

@login_required
def restore_order(request):
    """Restores the last deleted order from session."""
    if request.method == "POST":
        data = request.session.get('deleted_order')
        if not data:
            return HttpResponse(status=204) # Do nothing
            
        try:
            table = Table.objects.get(id=data['table_id'])
            item = Item.objects.get(id=data['item_id']) if data['item_id'] else None
            
            Order.objects.create(
                table=table,
                item=item,
                description=data['description'],
                transaction_price=Decimal(data['price']),
                order_source=data['order_type'],
                is_paid=False
            )
            
            # Clear session
            del request.session['deleted_order']
            
            # Return Updates
            _get_table_context(table)
            
            from django.template.loader import render_to_string
            card_html = render_to_string('manager/partials/table_card.html', {
                'table': table,
                'is_oob': True,
                'suppress_messages': True
            }, request=request)
             
            toast_html = render_to_string('manager/partials/toast_notification.html', {
                'message': _("Order restored!"),
                'level': 'success'
            }, request=request)
            
            return HttpResponse(card_html + toast_html)
            
        except Exception:
            pass
            
    return HttpResponse(status=204)

@login_required
def serve_all_orders(request, table_id):
    """Marks all current active orders for a table as served."""
    if request.method == "POST":
        table = get_object_or_404(Table, id=table_id)
        Order.objects.filter(table=table, is_paid=False).update(is_served=True)
        _get_table_context(table)
        return render(request, 'manager/partials/table_card.html', {'table': table})
    return redirect('dashboard')

@superuser_required
def daily_receipt(request, year, month, day):
    """Render a receipt-like page for a given date listing totals aggregated by table."""
    if not request.user.is_superuser:
        return redirect('unauthorized')
    import datetime
    from django.db.models import Sum, Q, Prefetch

    try:
        target_date = datetime.date(year, month, day)
    except ValueError:
        return redirect('session_history')

    # Get all paid orders for this date
    all_paid_orders = list(Order.objects.filter(
        is_paid=True, 
        timestamp__date=target_date
    ).select_related('item', 'table').order_by('table__number'))
    
    # Get all sessions in one query
    sessions = list(TableSession.objects.filter(check_out_time__date=target_date))
    
    table_aggregation = {}

    for o in all_paid_orders:
        t_num = o.table.number
        if t_num not in table_aggregation:
            table_aggregation[t_num] = {
                'table': t_num,
                'drink': 0, 'food': 0, 'print_bw': 0, 'print_color': 0,
                'fax': 0, 'copy': 0, 'min_charge': 0, 'other': 0,
                'total': 0,
                'items_total_price': 0
            }
        
        row = table_aggregation[t_num]
        price = o.transaction_price if o.transaction_price is not None else (o.item.price if o.item else Decimal('0.00'))
        price = price or Decimal('0.00')
        desc = (o.description or "").lower()
        item_name = o.item.name if o.item else "Custom Service"
        
        row['items_total_price'] += price
        
        is_drink = o.item.is_drink if o.item else False

        if o.item is None:
            row['other'] += price
        elif is_drink:
            row['drink'] += price
        elif item_name == "Printing Service":
            if "color" in desc:
                row['print_color'] += price
            else:
                row['print_bw'] += price
        elif item_name == "Fax Service":
            row['fax'] += price
        elif item_name == "Copy Service":
            row['copy'] += price
        else:
            row['food'] += price

    for s in sessions:
        t_num = s.table_number
        if t_num not in table_aggregation:
            table_aggregation[t_num] = {
                'table': t_num,
                'drink': 0, 'food': 0, 'print_bw': 0, 'print_color': 0,
                'fax': 0, 'copy': 0, 'min_charge': 0, 'other': 0,
                'total': 0,
                'items_total_price': 0
            }
        table_aggregation[t_num]['total'] += s.total_amount

    categorized_sessions = []
    totals = {
        'drink': 0, 'food': 0, 'print_bw': 0, 'print_color': 0,
        'fax': 0, 'copy': 0, 'min_charge': 0, 'other': 0, 'final': 0
    }

    sorted_keys = sorted(table_aggregation.keys(), key=lambda x: int(x) if str(x).isdigit() else 0)

    for t_num in sorted_keys:
        row = table_aggregation[t_num]
        if t_num == 0:
            row['total'] = row['items_total_price']
            row['min_charge'] = Decimal('0.00')
        else:
            if row['total'] < row['items_total_price']:
                row['total'] = row['items_total_price']
            row['min_charge'] = row['total'] - row['items_total_price']
        categorized_sessions.append(row)
        
        for key in totals:
            if key == 'final':
                totals['final'] += row['total']
            else:
                totals[key] += row[key]

    return render(request, 'manager/receipt.html', {
        'target_date': target_date,
        'categorized_orders': categorized_sessions,
        'category_totals': totals,
        'sessions': sessions,
        'sessions_total': totals['final'],
    })

@superuser_required
def clear_data(request):
    """View to clear old order and session data up to a selected date."""
    if request.method == "POST":
        until_date_str = request.POST.get('until_date')
        clear_all = request.POST.get('clear_all') == 'on' 
        
        if not until_date_str:
            messages.error(request, _("Please select a date."))
            return redirect('session_history')
        
        try:
            # More robust parsing to avoid 500 errors on some Windows 7 locales
            y, m, d = map(int, until_date_str.split('-'))
            until_date = datetime.date(y, m, d)
            # Create end-of-day datetime
            naive_dt = datetime.datetime.combine(until_date, datetime.time.max)
            until_dt = timezone.make_aware(naive_dt)
            
            # print(f"[CLEANUP] Executing delete up to {until_dt} (Clear All: {clear_all})")
            
            # 1. Delete Orders
            if clear_all:
                orders_count, deleted_info = Order.objects.filter(timestamp__lte=until_dt).delete()
            else:
                orders_count, deleted_info = Order.objects.filter(is_paid=True, timestamp__lte=until_dt).delete()
            
            # 2. Delete TableSessions
            sessions_count, deleted_info = TableSession.objects.filter(check_out_time__lte=until_dt).delete()
            
            messages.success(request, _("Cleanup Complete: Deleted %(orders)d orders and %(sessions)d sessions up to %(date)s.") % {
                'orders': orders_count,
                'sessions': sessions_count,
                'date': until_date_str
            })
            
        except Exception as e:
            # print(f"[CLEANUP ERROR] {str(e)}")
            messages.error(request, _("An error occurred during cleanup: %(error)s") % {'error': str(e)})
            
    # Redirect back to the referrer (history page) or fallback to today's history
    return redirect(request.META.get('HTTP_REFERER', 'session_history'))

@login_required
def dismiss_table(request, table_id):
    """Resets the table and deletes all its unpaid orders without saving to history."""
    if request.method == "POST":
        table = get_object_or_404(Table, id=table_id)
        
        # 1. Delete all unpaid orders for this table
        table.order_set.filter(is_paid=False).delete()
        
        # 2. Reset the table
        if int(table.number) != 0:
            table.is_occupied = False
            table.current_people = 0
        else:
            # Table 0 is special, just reset metadata
            table.is_occupied = True
            table.current_people = 1
            table.opened_at = timezone.now()
            
        table.save()
        messages.info(request, _("Table %(number)s has been dismissed.") % {'number': table.number})
        
        if request.headers.get('HX-Request'):
            # Return full grid to re-sort if necessary
            tables = _get_sorted_tables()
            return render(request, 'manager/partials/table_grid.html', {'tables': tables})
            
    return redirect('dashboard')
