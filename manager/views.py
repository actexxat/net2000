from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest

from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import models
from django.db.models import Sum, Q, Prefetch, Avg, Count, Max, Min, F, ExpressionWrapper, fields
from django.db.models.functions import Coalesce, ExtractHour, ExtractWeekDay
from .models import Table, Item, Order, TableSession, StickyNote, QuickFireItem
from infrastructure.models import GlobalSettings
from decimal import Decimal, InvalidOperation

import re, datetime, json
from django.utils.translation import gettext_lazy as _, get_language, get_language
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.urls import reverse


def _loc(val):
    from django.utils.translation import get_language
    is_ar = get_language() == 'ar'
    if not is_ar: return str(val)
    return str(val).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))

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

def log_action(user, action_type, details, table=None):
    from .models import ActionLog
    try:
        ActionLog.objects.create(
            user=user if user.is_authenticated else None,
            action_type=action_type,
            details=details,
            table=table
        )
    except Exception:
        pass


def _activate_language(request):
    """
    Centralized helper to activate language for a request.
    Prioritizes explicit 'lang' parameter, then cookie/session detection.
    """
    from django.utils import translation
    lang = request.GET.get('lang') or request.POST.get('lang')
    if not lang:
        lang = translation.get_language_from_request(request)
    translation.activate(lang)
    request.LANGUAGE_CODE = translation.get_language()
    return lang

@login_required
def unauthorized(request):
    """Returns a nice-looking access denied page."""
    return render(request, 'manager/unauthorized.html')

def _get_table_context(table, settings=None):
    """
    Internal helper to calculate table totals and attach them to the object.
    Uses centralized model logic for consistency.
    """
    if table.is_occupied:
        summary = table.get_bill_summary(settings)
        
        # Attach variables for templates
        table.orders = summary['orders']
        table.actual_orders = summary['order_total']
        table.shortfall = summary['shortfall']
        table.final_total = summary['final_total']
        table.total_price = summary['final_total'] # Alias for template compatibility
        table.min_charge_progress = summary['progress']
    else:
        table.actual_orders = 0
        table.shortfall = 0
        table.final_total = 0
        table.min_charge_progress = 0
    return table

def _get_sorted_tables(sort_by_status=True):
    """Helper to get all tables sorted by status, with contexts prepared."""
    from django.db.models import Prefetch
    from .models import Table, Order, Item
    from infrastructure.models import GlobalSettings
    
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

    settings, created = GlobalSettings.objects.get_or_create(id=1)
    for table in tables:
        _get_table_context(table, settings)
        
    return tables

def _get_grouped_items():
    """Helper to group items by category for the menu."""
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
    return grouped_items

def _get_quick_items():
    """Helper to get the quick fire items for the bar."""
    db_items = list(QuickFireItem.objects.all().order_by('order').select_related('item'))
    
    if db_items:
        quick_items = [q.item for q in db_items]
    else:
        # Fallback to hardcoded list if DB is empty (legacy support)
        items = Item.objects.all()
        quick_items = []
        target_names = ["turkish coffee", "tea", "water", "latte", "redbull", "twist", "v cola", "sun top", "volt", "nescafe"]
        
        # 1. Fetch prefered items in order
        for name_query in target_names:
            # fuzzy match or exact match logic
            found = next((i for i in items if name_query in i.name.lower()), None)
            if found and found not in quick_items:
                quick_items.append(found)

    # 2. Fill remainder with top sellers if needed (up to 12 items for bar)
    # Only run this if we are in fallback mode (no admin items specified)
    if not db_items and len(quick_items) < 12:
        top_ids = Order.objects.filter(item__isnull=False).values('item').annotate(c=Count('id')).order_by('-c')[:12]
        for t in top_ids:
            try:
                candidate = Item.objects.get(id=t['item'])
                if candidate not in quick_items:
                    quick_items.append(candidate)
            except Item.DoesNotExist:
                continue
    
    # Limit to reasonable number
    return quick_items[:12]

@login_required
def dashboard(request):
    """Main view to see all tables and their current bills."""
    from django.db.models import Prefetch
    
    tables = _get_sorted_tables()
    
    settings, created = GlobalSettings.objects.get_or_create(id=1)
    
    # Items grouping logic...
    
    grouped_items = _get_grouped_items()
    
    # Get the global minimum charge (creates a default of 25 if none exists)
    # Quick Fire Items (Top 5 selling)
    # Manually curated list for Quick Fire bar (priority items)
    # Now fetched from the database (QuickFireItem model)
    quick_items = _get_quick_items()

    # Sticky Notes
    notes = StickyNote.objects.all().select_related('author').order_by('-created_at')

    return render(request, 'manager/dashboard.html', {
        'tables': tables,
        'grouped_items': grouped_items,
        'quick_items': quick_items,
        'notes': notes,
        'global_min_charge': settings.min_charge_per_person,
        'server_now': timezone.now().isoformat()
    })

def _get_dashboard_grid_state_string(request):
    """Helper to generate a state string for the dashboard grid."""
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
    
    # Handle None values from Sum on empty sets
    s_cnt = orders_agg['served_cnt'] or 0
    p_sum = tables_agg['people_sum'] or 0
    
    # v16-localization: Force activate language using centralized helper
    user_language = _activate_language(request)
    # print(f"DEBUG: polling grid. Lang detected: {user_language}")

    notes_agg = StickyNote.objects.aggregate(cnt=Count('id'), last_upd=Max('updated_at'))
    n_upd = notes_agg['last_upd'].isoformat() if notes_agg['last_upd'] else 'none'
    
    # Create a unique state string
    # v17-layout: Force refresh after layout changes (hero height)
    lang = user_language
    state_str = f"{orders_agg['cnt']}-{orders_agg['max_id']}-{s_cnt}-{tables_agg['occupied_cnt']}-{p_sum}-{notes_agg['cnt']}-{n_upd}-{lang}-v17-layout"
    return state_str

@login_required
def dashboard_grid(request):
    """Returns OOB updates for all tables to update them in-place."""
    import hashlib
    from django.http import HttpResponse, HttpResponseNotModified
    from django.template.loader import render_to_string
    
    state_str = _get_dashboard_grid_state_string(request)
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
    notes = StickyNote.objects.all().select_related('author').order_by('-created_at')
    
    content = render_to_string('manager/partials/table_grid_premium.html', {
        'tables': tables,
        'notes': notes
    }, request=request)
    
    response = HttpResponse(content)
    response['ETag'] = f'"{et}"'
    return response

@login_required
def notification_history(request):
    """Returns a partial list of recent QR orders."""
    _activate_language(request)
    # filtering for QR orders
    qr_orders = Order.objects.filter(order_source='QR').order_by('-timestamp')[:20].select_related('table', 'item')
    return render(request, 'manager/partials/notification_history.html', {'orders': qr_orders})

@login_required
def check_in(request, table_id):
    """Marks a table as occupied. Accepts people_count from POST if provided."""
    _activate_language(request)
    
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
        messages.success(request, _("Table %(number)s opened successfully") % {'number': table.number})
        
        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            from django.http import HttpResponse
            
            # Return full grid to re-sort
            tables = _get_sorted_tables()
            grid_html = render_to_string('manager/partials/table_grid_premium.html', {'tables': tables}, request=request)
            
            # Render messages popup for instant display
            messages_html = render_to_string('manager/partials/messages.html', {}, request=request)
            
            return HttpResponse(grid_html + messages_html)
            
    return redirect('dashboard')

@login_required
def refresh_table(request, table_id):
    """Returns a single table card for targeted UI updates."""
    _activate_language(request)
    table = get_object_or_404(Table, id=table_id)
    _get_table_context(table)
    return render(request, 'manager/partials/table_card.html', {'table': table})

@login_required
def update_people(request, table_id):
    """Updates the number of people at a table from the card input."""
    _activate_language(request)
    
    if request.method == "POST":
        table = get_object_or_404(Table, id=table_id)
        table.current_people = int(request.POST.get('people_count', 1))
        table.save()
        # Message removed to prevent popup queueing
        
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
    _activate_language(request)
    
    table = get_object_or_404(Table, id=table_id)

    if request.method == "GET":
        # logic to populate menu items for the modal
        grouped_items = _get_grouped_items()
         
        _get_table_context(table)
        
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
            
            # Log action
            log_details = f"Added {len(added_items)} items: {', '.join(added_items)}"
            log_action(request.user, 'ORDER', log_details, table)
        else:
            messages.error(request, _("Failed to add items to bill."))
            
        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            from django.http import HttpResponse
            
            _get_table_context(table)
            card_html = render_to_string('manager/partials/table_card.html', {'table': table}, request=request)
            messages_html = render_to_string('manager/partials/messages.html', {}, request=request)
            return HttpResponse(card_html + messages_html)
            
    return redirect('dashboard')

def _create_table_session(table, summary, user):
    """Helper to create a TableSession from a table and bill summary."""
    final_bill = summary['final_total']
    
    items_list = []
    for order in summary['orders']:
        name = order.item_name_display
        note = order.customer_note_display
        items_list.append(f"{name} [{note}]" if note else name)

    items_summary = ", ".join(items_list) if items_list else "No items ordered"
        
    # 1. Save record to history
    settings, created = GlobalSettings.objects.get_or_create(id=1)
    TableSession.objects.create(
        table_number=table.number,
        people_count=table.current_people,
        items_summary=items_summary,
        total_amount=final_bill,
        check_in_time=table.opened_at or timezone.now(),
        shift=settings.active_shift,
        user=user
    )
    return final_bill

@login_required
def check_out(request, table_id):
    """Calculates final total, saves to history, and resets the table."""
    table = get_object_or_404(Table, id=table_id)
    summary = table.get_bill_summary()
    
    final_bill = _create_table_session(table, summary, request.user)
    
    # 2. Reset the table and mark orders as paid
    settings, created = GlobalSettings.objects.get_or_create(id=1)
    table.order_set.filter(is_paid=False).update(is_paid=True, shift=settings.active_shift, paid_at=timezone.now())
    
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
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        
        _get_table_context(table, settings)
        card_html = render_to_string('manager/partials/table_card.html', {'table': table}, request=request)
        
        # Render messages popup for instant display
        messages_html = render_to_string('manager/partials/messages.html', {}, request=request)
        
        response = HttpResponse(card_html + messages_html)
        response['HX-Trigger'] = 'close-modal, refresh'
        return response
        
    return redirect('dashboard')

def _get_growth_metrics(today):
    """Helper to calculate growth metrics."""
    import datetime
    
    # Define start and end of today in local timezone
    start_of_today = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
    end_of_today = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))

    # Define start and end of last week day in local timezone
    last_week_day = today - datetime.timedelta(days=7)
    start_of_last_week_day = timezone.make_aware(datetime.datetime.combine(last_week_day, datetime.time.min))
    end_of_last_week_day = timezone.make_aware(datetime.datetime.combine(last_week_day, datetime.time.max))

    today_sessions = TableSession.objects.filter(check_out_time__range=(start_of_today, end_of_today))
    last_week_sessions = TableSession.objects.filter(check_out_time__range=(start_of_last_week_day, end_of_last_week_day))
    
    today_rev = today_sessions.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    last_week_rev = last_week_sessions.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    
    growth = 0
    if last_week_rev > 0:
        growth = ((today_rev - last_week_rev) / last_week_rev) * 100
    
    return growth, today_rev, last_week_rev


@login_required
@superuser_required
def metrics_dashboard(request):
    """
    Renders the metrics dashboard with various statistics.
    """
    _activate_language(request)
    now = timezone.now()
    today = now.date()

    growth, today_rev, last_week_rev = _get_growth_metrics(today)

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
    today_sessions = TableSession.objects.filter(check_out_time__date=today)
    opening_time = today_sessions.aggregate(m=Min('check_in_time'))['m']
    closing_time = today_sessions.aggregate(m=Max('check_out_time'))['m']

    # 5. Month-to-Date Revenue (Replaces Total Transactions)
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_revenue = TableSession.objects.filter(check_out_time__gte=this_month_start).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    # 6. Highest Bill Today (Replaces Occupancy Rate)
    highest_bill = today_sessions.aggregate(Max('total_amount'))['total_amount__max'] or Decimal('0.00')

    # Top selling items
    top_selling_items = Order.objects.filter(is_paid=True, item__isnull=False).values('item__name').annotate(
        total_quantity=Count('item__name'),
        total_revenue=Sum('transaction_price')
    ).order_by('-total_quantity', '-total_revenue')[:5]

    top_selling_items = [
        {
            'name': item['item__name'],
            'quantity': _loc(item['total_quantity']),
            'revenue': _loc(f"{item['total_revenue']:.2f}")
        }
        for item in top_selling_items
    ]

    # Category data
    category_data_raw = Order.objects.filter(is_paid=True, item__isnull=False).values('item__category').annotate(
        total_revenue=Sum('transaction_price')
    ).order_by('-total_revenue')

    category_labels = []
    category_revenues = []
    for category in category_data_raw:
        category_labels.append(category['item__category'] or _("Uncategorized"))
        category_revenues.append(float(category['total_revenue'] or 0))

    category_data = {
        'labels': json.dumps(category_labels),
        'data': json.dumps(category_revenues)
    }

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

    # 7. Busiest Hour Today (Replaces Traffic Prediction)
    peak_hour_data = today_sessions.annotate(h=ExtractHour('check_out_time')).values('h').annotate(r=Sum('total_amount')).order_by('-r').first()
    
    if peak_hour_data:
        ph = peak_hour_data['h']
        ampm = _('AM') if ph < 12 else _('PM')
        display_h = (ph % 12) or 12
        busiest_hour = f"{display_h} {ampm}"
        busiest_rev = peak_hour_data['r']
    else:
        busiest_hour = "--"
        busiest_rev = 0
    
    is_ar = get_language() == 'ar' # Define is_ar here
    
    return render(request, 'manager/metrics.html', {
        'month_revenue': _loc(f"{month_revenue:.2f}"),
        'month_name': now.strftime('%B'),
        'growth': round(growth, 1),
        'top_items': top_selling_items,
        'category_data': category_data_raw,
        'avg_duration': avg_dur_str,
        'avg_bill': _loc(f"{avg_bill:.2f}"),
        'avg_per_person': _loc(f"{avg_per_person:.2f}"),
        'highest_bill_today': _loc(f"{highest_bill:.2f}"),
        'opening_time': timezone.localtime(opening_time).strftime('%H:%M') if opening_time else "--:--",
        'closing_time': timezone.localtime(closing_time).strftime('%H:%M') if closing_time else "--:--",
        'today_bw': _loc(today_bw),
        'today_color': _loc(today_color),
        'top_tables': top_tables,
        'busiest_hour': _loc(busiest_hour),
        'busiest_rev': _loc(f"{busiest_rev:.0f}"),
        'hours_labels': json.dumps(hours_labels),
        'hours_data_rev': json.dumps(hours_data_rev),
        'is_ar': is_ar,
    })

@login_required
@superuser_required
def session_history(request):
    """View list of past paid sessions."""
    _activate_language(request)
    import datetime
         
    date_str = request.GET.get('date')
    shift_filter = request.GET.get('shift', 'MORNING') # Default to morning tab

    if date_str:
        try:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
             selected_date = timezone.localtime(timezone.now()).date()
    else:
        selected_date = timezone.localtime(timezone.now()).date()

    # Robust Range Filtering: 
    start_local = datetime.datetime.combine(selected_date, datetime.time.min)
    end_local = datetime.datetime.combine(selected_date, datetime.time.max)
    
    # Ensure timezone awareness
    current_tz = timezone.get_current_timezone()
    start_aware = timezone.make_aware(start_local, current_tz)
    end_aware = timezone.make_aware(end_local, current_tz)

    sessions = TableSession.objects.filter(
        check_out_time__range=(start_aware, end_aware),
        shift=shift_filter
    ).order_by('-check_out_time')
    
    is_ar = get_language() == 'ar'
    def _loc(val):
        if not is_ar: return str(val)
        return str(val).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))
        
    loc_sessions = []
    total_revenue = Decimal('0.00')
    for s in sessions:
        total_revenue += s.total_amount
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
        'prev_date': (selected_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
        'next_date': (selected_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
        'total_count': _loc(sessions.count()),
        'total_revenue': _loc(f"{total_revenue:.2f}"),
        'active_shift_tab': shift_filter,
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
    _activate_language(request)

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
            
            # Log action
            log_action(request.user, 'PRINT', name, table)

            messages.success(request, _("Added %(name)s to Table %(number)s.") % {'name': name, 'number': table.number})
        except Exception:
            messages.error(request, _("Failed to add print to bill."))
            
        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            from django.http import HttpResponse
            
            _get_table_context(table)
            card_html = render_to_string('manager/partials/table_card.html', {'table': table}, request=request)
            messages_html = render_to_string('manager/partials/messages.html', {}, request=request)
            return HttpResponse(card_html + messages_html)
            
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
        
    # Standardize data via Prefetch
    unpaid_orders_prefetch = Prefetch(
        'order_set',
        queryset=Order.objects.filter(is_paid=False).select_related('item').order_by('timestamp'),
        to_attr='active_orders'
    )
    tables = Table.objects.filter(is_occupied=True).prefetch_related(unpaid_orders_prefetch).order_by('number')
    all_tables = Table.objects.all().order_by('number')
    
    busy_tables = []
    total_people = 0
    total_due = Decimal('0.00')

    for table in tables:
        summary = table.get_bill_summary()
        
        # Format orders for template
        orders_data = []
        for o in summary['orders']:
            price = o.transaction_price if o.transaction_price is not None else (o.item.price if o.item else Decimal('0.00'))
            orders_data.append({
                'name': o.item_name_display,
                'category': o.item_category_display,
                'note': o.customer_note_display,
                'price': price or Decimal('0.00')
            })

        busy_tables.append({
            'id': table.id,
            'number': table.number,
            'people': table.current_people,
            'orders': orders_data,
            'order_total': summary['order_total'],
            'shortfall': summary['shortfall'],
            'final_total': summary['final_total'],
        })

        total_people += table.current_people
        total_due += summary['final_total']

    context = {
        'busy_count': len(busy_tables),
        'busy_tables': busy_tables,
        'total_people': total_people,
        'total_due': total_due,
        'all_tables': all_tables,
    }
    return render(request, 'manager/monitor.html', context)

@login_required
def log_modal(request):
    """Returns the log modal content."""
    from .models import ActionLog
    logs = ActionLog.objects.all()[:100]
    return render(request, 'manager/partials/modals/log_modal.html', {'logs': logs})

@login_required
@superuser_required
def clear_log(request):
    """Clears the action log."""
    from .models import ActionLog
    if request.method == "POST":
        ActionLog.objects.all().delete()
    return log_modal(request)

@require_POST
@login_required
def add_order_direct(request, table_id):
    """
    Instantly adds a single item to the table order via HTMX.
    """
    _activate_language(request)
    
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
    
    # Log action
    log_action(request.user, 'ORDER', f"Added {item.name} ({price} EGP)", table)
    
    # Refresh table context for the card update
    settings, created = GlobalSettings.objects.get_or_create(id=1)
    _get_table_context(table, settings)
    
    # Render the updated table card
    card_html = render_to_string('manager/partials/table_card.html', {
        'table': table, 
        'is_oob': True,
        'suppress_messages': True
    }, request=request)
    
    # 2. Add message 
    messages.success(request, _("Added %(item)s to Table %(number)s") % {'item': item.name, 'number': table.number})
    # Render messages popup for instant display
    messages_html = render_to_string('manager/partials/messages.html', {}, request=request)
    
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
    
    return HttpResponse(card_html + messages_html + live_list_html + badge_html)


@require_POST
@login_required
def add_fax(request, table_id):
    _activate_language(request)
    
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
    
    # Log action
    log_action(request.user, 'FAX', desc_str, table)

    messages.success(request, _("Added Fax (%(pages)s pages) to Table %(number)s. Cost: %(cost)s") % {
        'pages': pages, 
        'number': table.number,
        'cost': price
    })
    
    if request.headers.get('HX-Request'):
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        
        _get_table_context(table)
        card_html = render_to_string('manager/partials/table_card.html', {'table': table}, request=request)
        messages_html = render_to_string('manager/partials/messages.html', {}, request=request)
        return HttpResponse(card_html + messages_html)
        
    return redirect('dashboard')


    return redirect('dashboard')


@require_POST
@login_required
def add_copy(request, table_id):
    """Handle manual copy orders with user-defined cost."""
    _activate_language(request)
    
    table = get_object_or_404(Table, id=table_id)
    
    try:
        pages = int(request.POST.get('pages', 0))
    except (ValueError, TypeError):
        pages = 0
        
    # Cafe only supports B/W copying
    if True:
        # Tiered pricing: <=100 pages -> 1.00 EGP, >100 pages -> 0.75 EGP
        if pages <= 100:
            ppp = Decimal('1.00')
        else:
            ppp = Decimal('0.75')
        total = (Decimal(pages) * ppp).quantize(Decimal('0.01'))
        type_str = _("B/W")
    
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
        
        # Log action
        log_action(request.user, 'COPY', name, table)

        messages.success(request, _("Added %(name)s to Table %(number)s. Cost: %(cost)s") % {
            'name': name, 
            'number': table.number,
            'cost': total
        })
    except Exception:
        messages.error(request, _("Failed to add copy to bill."))
        
    if request.headers.get('HX-Request'):
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        
        _get_table_context(table)
        card_html = render_to_string('manager/partials/table_card.html', {'table': table}, request=request)
        messages_html = render_to_string('manager/partials/messages.html', {}, request=request)
        return HttpResponse(card_html + messages_html)
        
    return redirect('dashboard')

@login_required
def service_modal_preview(request, table_id, service_type):
    """Returns the dynamic content for a specific service modal."""
    _activate_language(request)
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
    _activate_language(request)
    table = get_object_or_404(Table, id=table_id)
    
    cat = request.POST.get('custom_category', 'other')
    if cat == 'food':
        item_name = "Food"
    elif cat == 'fax':
        item_name = "Fax"
    elif cat == 'computer':
        item_name = "Computer"
    elif cat == 'internet':
        item_name = "Internet Service"
    else:
        item_name = request.POST.get('item_name', '').strip() or _("Custom Service")
        
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
        
        # Log action
        log_action(request.user, 'CUSTOM', f"Added {item_name} ({price} EGP)", table)

        messages.success(request, _("Added '%(name)s' to Table %(number)s. Price: %(price)s") % {
            'name': item_name, 
            'number': table.number,
            'price': price
        })
    except Exception:
        messages.error(request, _("Failed to add custom item to bill."))
        
    if request.headers.get('HX-Request'):
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        
        _get_table_context(table)
        card_html = render_to_string('manager/partials/table_card.html', {'table': table}, request=request)
        messages_html = render_to_string('manager/partials/messages.html', {}, request=request)
        return HttpResponse(card_html + messages_html)
        
    return redirect('dashboard')


@login_required
def checkout_preview(request, table_id):
    """
    Returns the partial HTML for the checkout modal with dynamic totals.
    """
    _activate_language(request)
    table = get_object_or_404(Table, id=table_id)
    global_settings = GlobalSettings.objects.first()
    
    # Calculate totals using the same logic as checkout
    # _get_table_context returns the table object with attached attributes
    ctx = _get_table_context(table, global_settings)
    
    # Pass all context variables needed for the modal
    context = {
        'table': table,
        'actual_orders_list': getattr(ctx, 'orders', []),
        'total_orders_price': getattr(ctx, 'actual_orders', 0),
        'shortfall': getattr(ctx, 'shortfall', 0),
        'final_total': getattr(ctx, 'final_total', 0),
    }
    return render(request, 'manager/partials/checkout_modal_content.html', context)

@login_required
def toggle_served(request, order_id):
    """Toggles the is_served status of an order via HTMX."""
    _activate_language(request)
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
    _activate_language(request)
    
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
        
        # Log action
        log_action(request.user, 'DISCARD', f"Discarded: {item_name} ({order.transaction_price} EGP)", table)

        order.delete()
        
        if table:
            _get_table_context(table)
            
            if request.headers.get('HX-Request'):
                target = request.headers.get('HX-Target')
                
                # Check target context
                is_modal_update = target == 'items-modal-inner'
                is_card_primary = target and target.startswith('table-card-')
                
                html_response = ""
                
                # 1. Table Card (OOB if modal is primary)
                card_html = render_to_string('manager/partials/table_card.html', {
                    'table': table,
                    'is_oob': is_modal_update or not is_card_primary, 
                    'suppress_messages': True
                }, request=request)
                
                if is_modal_update:
                    # Return Modal Inner Content as primary
                    modal_html = render_to_string('manager/partials/items_popup_inner.html', {'table': table}, request=request)
                    html_response = modal_html + card_html # Card is OOB
                elif is_card_primary:
                    # Card is primary
                    html_response = card_html
                else:
                    # Fallback (Live List logic - unlikely used but keeping safe)
                    html_response = card_html # Default to card OOB and live list primary? 
                    # Actually, if target is unknown, usually card update is safer.
                    # But keeping original logic flow if possible:
                    pass

                # If we are NOT modal update, stick to original logic order?
                if not is_modal_update:
                     # Original Logic Reconstruction:
                     # If target starts with table-card, card is primary.
                     # Else... logic was slightly obscure in original.
                     # Let's simplify: Always return Card OOB if we return something else.
                     
                     if not is_card_primary:
                         # Assume Live List update (for Monitor page?)
                         active_orders = table.order_set.filter(is_paid=False).select_related('item').order_by('-timestamp')
                         live_list_html = render_to_string('manager/partials/live_order_list.html', {
                            'orders': active_orders,
                            'table': table,
                            'is_oob': False # Primary
                         }, request=request)
                         html_response = live_list_html + card_html
                     else:
                         html_response = card_html

                # 3. Badge Update (Always OOB)
                # ... (Keeping existing badge logic but simpler)
                active_orders = table.order_set.filter(is_paid=False)
                from manager.templatetags.manager_extras import translate_numbers
                count_loc = translate_numbers(active_orders.count())
                badge_html = f'<span class="badge bg-danger rounded-pill" id="live-order-badge" hx-swap-oob="true">{count_loc}</span>'
                
                # 4. Message with UNDO button
                msg = _("Removed %(item)s") % {'item': item_name}
                action_html = f"""
                <button class='btn btn-sm btn-light ms-2 py-0 fw-bold' 
                        hx-post='/restore-order/' 
                        hx-swap='none'
                        onclick='this.closest(".message-popup").remove()'>
                    { _('UNDO') }
                </button>
                """
                messages.success(request, f"{msg} {action_html}")
                
                # Render messages popup
                messages_html = render_to_string('manager/partials/messages.html', {}, request=request)
                
                return HttpResponse(html_response + badge_html + messages_html)
            
            # Fallback for non-HTMX
            messages.success(request, _("Item removed: %(item)s") % {'item': item_name})
            return render(request, 'manager/partials/table_card.html', {'table': table})
            
    return redirect('dashboard')

@login_required
def restore_order(request):
    """Restores the last deleted order from session."""
    _activate_language(request)
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
    _activate_language(request)
    if request.method == "POST":
        table = get_object_or_404(Table, id=table_id)
        Order.objects.filter(table=table, is_paid=False).update(is_served=True)
        _get_table_context(table)
        return render(request, 'manager/partials/table_card.html', {'table': table})
    return redirect('dashboard')

@login_required
def item_popup_preview(request, table_id):
    """
    Returns HTML for the items popup modal.
    """
    _activate_language(request)
    table = get_object_or_404(Table, id=table_id)
    _get_table_context(table)
    return render(request, 'manager/partials/items_popup.html', {'table': table})

@superuser_required
def daily_receipt(request, year, month, day):
    """Render a receipt-like page for a given date listing totals aggregated by table."""
    _activate_language(request)
    if not request.user.is_superuser:
        return redirect('unauthorized')
    import datetime
    from django.db.models import Sum, Q, Prefetch

    try:
        target_date = datetime.date(year, month, day)
    except ValueError:
        return redirect('session_history')

    # Shift Filter
    shift_filter = request.GET.get('shift')

    # Get all paid orders for this date
    # Use paid_at if available (correct for crossovers), fallback to timestamp for old data
    order_filter = Q(is_paid=True) & (Q(paid_at__date=target_date) | Q(paid_at__isnull=True, timestamp__date=target_date))
    session_filter = Q(check_out_time__date=target_date)
    
    # User asked for "reports separately for each shift".
    # Only show itemized orders if NO shift filter is applied, 
    # OR if we want to add a shift field to Order (more complex).
    # For now, we filter sessions by shift.
    if shift_filter in ['MORNING', 'NIGHT']:
        session_filter &= Q(shift=shift_filter)
        order_filter &= Q(shift=shift_filter)

    all_paid_orders = list(Order.objects.filter(order_filter).select_related('item', 'table').order_by('table__number'))
    
    # Get all sessions in one query
    sessions = list(TableSession.objects.filter(session_filter))
    
    table_aggregation = {}

    for o in all_paid_orders:
        t_num = o.table.number
        if t_num not in table_aggregation:
            table_aggregation[t_num] = {
                'table': t_num,
                'drink': 0, 'food': 0, 'fax': 0, 'print_bw': 0, 'print_color': 0,
                'copy_bw': 0, 'min_charge': 0, 'other': 0, 'internet': 0,
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

        is_color = "color" in desc or "ألوان" in desc
        
        if o.item is None:
            if o.description == "Food":
                row['food'] += price
            elif o.description == "Fax":
                row['fax'] += price
            elif o.description == "Internet Service":
                row['internet'] += price
            else:
                row['other'] += price
        elif is_drink:
            row['drink'] += price
        elif item_name == "Printing Service":
            if is_color:
                row['print_color'] += price
            else:
                row['print_bw'] += price
        elif item_name == "Fax Service" or item_name == "Fax":
            row['fax'] += price
        elif item_name == "Copy Service":
            row['copy_bw'] += price
        else:
            row['food'] += price

    for s in sessions:
        t_num = s.table_number
        if t_num not in table_aggregation:
            table_aggregation[t_num] = {
                'table': t_num,
                'drink': 0, 'food': 0, 'print_bw': 0, 'print_color': 0,
                'fax': 0, 'copy_bw': 0, 'min_charge': 0, 'other': 0,
                'total': 0,
                'items_total_price': 0
            }
        table_aggregation[t_num]['total'] += s.total_amount

    categorized_sessions = []
    totals = {
        'drink': Decimal('0.00'), 'food': Decimal('0.00'), 'fax': Decimal('0.00'),
        'print_bw': Decimal('0.00'), 'print_color': Decimal('0.00'), 'copy_bw': Decimal('0.00'), 
        'min_charge': Decimal('0.00'), 'other': Decimal('0.00'), 'internet': Decimal('0.00'), 
        'final': Decimal('0.00')
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
            elif key == 'drink':
                totals['drink'] += row['drink']
            elif key == 'food':
                totals['food'] += row['food']
            elif key == 'fax':
                totals['fax'] += row['fax']
            elif key == 'print_bw':
                totals['print_bw'] += row['print_bw']
            elif key == 'print_color':
                totals['print_color'] += row['print_color']
            elif key == 'copy_bw':
                totals['copy_bw'] += row['copy_bw']
            elif key == 'min_charge':
                totals['min_charge'] += row['min_charge']
            elif key == 'other':
                totals['other'] += row['other']
            elif key == 'internet':
                totals['internet'] += row['internet']

    return render(request, 'manager/receipt.html', {
        'categorization_date': target_date,
        'categorized_orders': categorized_sessions,
        'category_totals': totals,
        'sessions': sessions,
        'sessions_total': totals['final'],
    })

@superuser_required
def clear_data(request):
    """View to clear old order and session data up to a selected date."""
    _activate_language(request)
    if request.method == "POST":
        until_date_str = request.POST.get('until_date')
        clear_all = request.POST.get('clear_all') == 'on'
        
        if not until_date_str:
            messages.error(request, _("Please select a date."))
            return redirect('session_history')
        
        try:
            # 1. Parse date and create a localized end-of-day boundary
            y, m, d = map(int, until_date_str.split('-'))
            until_date = datetime.date(y, m, d)
            
            # Combine with end of day time
            until_dt_naive = datetime.datetime.combine(until_date, datetime.time.max)
            # Make it timezone aware using the application's current timezone
            # (Africa/Cairo in settings.py)
            until_dt = timezone.make_aware(until_dt_naive, timezone.get_current_timezone())
            
            # 2. Delete Orders
            # We use the datetime boundary for precise inclusion
            if clear_all:
                orders_count, deleted_info = Order.objects.filter(timestamp__lte=until_dt).delete()
            else:
                # Normal cleanup: only delete orders that are finalized and paid
                orders_count, deleted_info = Order.objects.filter(is_paid=True, timestamp__lte=until_dt).delete()
            
            # 3. Delete TableSessions (History records)
            sessions_count, deleted_info = TableSession.objects.filter(check_out_time__lte=until_dt).delete()
            
            # 4. Optional: Full Reset
            if clear_all and until_date >= datetime.date.today():
                 # Wipe current active table states if deleting everything including today
                 Table.objects.all().update(is_occupied=False, current_people=1, opened_at=None)
            
            messages.success(request, _("Cleanup Complete: Deleted %(orders)d orders and %(sessions)d sessions up to %(date)s.") % {
                'orders': orders_count,
                'sessions': sessions_count,
                'date': until_date.strftime('%d/%m/%Y')
            })
            
        except Exception as e:
            messages.error(request, _("An error occurred during cleanup: %(error)s") % {'error': str(e)})
            
    return redirect(request.META.get('HTTP_REFERER', 'session_history'))

@login_required
def dismiss_table(request, table_id):
    """Resets the table and deletes all its unpaid orders without saving to history."""
    _activate_language(request)
    
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
        messages.success(request, _("Table %(number)s dismissed") % {'number': table.number})
        
        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            from django.http import HttpResponse
            
            # Return full grid to re-sort if necessary
            tables = _get_sorted_tables()
            grid_html = render_to_string('manager/partials/table_grid_premium.html', {'tables': tables}, request=request)
            
            # Render messages popup for instant display
            messages_html = render_to_string('manager/partials/messages.html', {}, request=request)
            
            return HttpResponse(grid_html + messages_html)
            
    return redirect('dashboard')

@login_required
@superuser_required
def switch_shift(request):
    """Toggles the current active shift. Tables remain open for manual handover."""
    _activate_language(request)
    if request.method == "POST":
        settings, created = GlobalSettings.objects.get_or_create(id=1)
        old_shift = settings.active_shift
        new_shift = 'NIGHT' if old_shift == 'MORNING' else 'MORNING'
        
        # Toggle the shift
        settings.active_shift = new_shift
        settings.save()
        
        msg = _("Shift started: Night Shift") if new_shift == 'NIGHT' else _("Shift started: Morning Shift")
        messages.success(request, msg)
        
    return redirect('dashboard')

@login_required
def add_sticky_note(request):
    import random
    colors = ['bg-soft-yellow', 'bg-soft-green', 'bg-soft-blue', 'bg-soft-purple', 'bg-soft-orange', 'bg-soft-red']
    note = StickyNote.objects.create(
        author=request.user,
        content='',
        color=random.choice(colors)
    )
    # Refresh the dashboard
    return HttpResponse(status=204, headers={'HX-Trigger': 'refresh'})

@login_required
def update_sticky_note(request, note_id):
    note = get_object_or_404(StickyNote, id=note_id)
    if request.method == 'POST':
        note.content = request.POST.get('content', '')
        note.save()
        return HttpResponse(status=204, headers={'HX-Trigger': 'refresh'})
    return HttpResponse(status=400)

@login_required
def delete_sticky_note(request, note_id):
    note = get_object_or_404(StickyNote, id=note_id)
    if note.author == request.user or request.user.is_superuser:
        note.delete()
        return HttpResponse(status=204, headers={'HX-Trigger': 'refresh'})
    return HttpResponse(status=403)

# Import update system views
from .update_views import (
    update_check_view,
    update_download_view,
    update_progress_view,
    update_apply_view,
    system_update_view
)
