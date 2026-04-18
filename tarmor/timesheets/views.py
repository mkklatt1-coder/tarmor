from django.contrib import messages
from django.db.models import Q
from django.forms import modelformset_factory
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import redirect, render
from personnel.models import Employee
from .forms import TimesheetAddForm, TimesheetEditForm
from .models import Timesheet
from work_orders.models import WorkOrder


def timesheets(request):
    return render(request, 'timesheets/timesheets.html')

def add_timesheet(request):
    TimesheetFormSet = modelformset_factory(
        Timesheet,
        form=TimesheetAddForm,
        extra=1
    )
    all_technicians = Employee.objects.all()
    next_url = request.GET.get("next") or request.POST.get("next")
    work_order_id = request.GET.get("work_order") or request.POST.get("work_order")
    if request.method == "POST":
        formset = TimesheetFormSet(
            request.POST,
            queryset=Timesheet.objects.none()
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, "Timesheet(s) added successfully!")
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("timesheets:timesheets")
        messages.error(request, "There was an error saving the timesheet. Please check the fields below.")
        print(formset.errors)
        print("WORK ORDER ID FROM URL/POST:", work_order_id)
    else:
        initial = []
        
        if work_order_id:
            initial.append({'work_order': work_order_id})
            
        formset = TimesheetFormSet(
            queryset=Timesheet.objects.none(),
            initial=initial
        )
        formset.extra = len(initial) if initial else 1
    return render(request, "timesheets/add_timesheet.html", {
        "formset": formset,
        "all_technicians": all_technicians,
        "next_url": next_url,
        "work_order_id": work_order_id,
    })
                
def edit_timesheet(request):
    work_order_query = request.GET.get('work_order', '').strip()
    technician_query = request.GET.get('technician', '').strip()
    queryset = Timesheet.objects.select_related('work_order', 'technician').all()
    if work_order_query:
        queryset = queryset.filter(work_order__work_order__icontains=work_order_query)
    if technician_query:
        queryset = queryset.filter(
            Q(technician__First_Name__icontains=technician_query) |
            Q(technician__Last_Name__icontains=technician_query)
        )
    TimesheetEditFormSet = modelformset_factory(Timesheet, form=TimesheetEditForm, extra=0)
    if request.method == "POST":
        work_order_query = request.POST.get('work_order_search', '').strip()
        technician_query = request.POST.get('technician_search', '').strip()
        queryset = Timesheet.objects.select_related('work_order', 'technician').all()
                
        if work_order_query:
            queryset = queryset.filter(work_order__work_order__icontains=work_order_query)
        if technician_query:
            name_filter = (
                Q(technician__First_Name__icontains=technician_query) |
                Q(technician__Last_Name__icontains=technician_query)
            )
            parts = technician_query.split()
            if technician_query and ' ' in technician_query:
                parts = technician_query.split()
                if len(parts) >= 2:
                    first = parts[0]
                    last = parts[-1]
                    queryset = queryset.filter(
                        Q(technician__First_Name__icontains=first, technician__Last_Name__icontains=last) |
                        Q(technician__First_Name__icontains=last, technician__Last_Name__icontains=first)
                    )
                queryset = queryset.filter(name_filter)
            
        formset = TimesheetEditFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Timesheet(s) updated successfully!")
            return redirect('timesheets:timesheets')
        else:
            messages.error(request, "There was an error updating the timesheet. Please check the fields below.")
    else:
        formset = TimesheetEditFormSet(queryset=queryset)
        
        all_work_orders = WorkOrder.objects.all().values_list('work_order', flat=True).distinct()
        all_technicians = Employee.objects.all()   
        
    return render(request, "timesheets/edit_timesheet.html", {
        "formset": formset,
        "work_order_query": work_order_query,
        "technician_query": technician_query,
        "all_work_orders": all_work_orders,
        "all_technicians": all_technicians,
    })
    
def search_timesheets(request):
    work_order_query = request.GET.get('work_order', '').strip()
    technician_query = request.GET.get('technician', '').strip()
    sort_by = request.GET.get('sort', 'work_order')
    queryset = Timesheet.objects.select_related('work_order', 'technician').all()
    
    if work_order_query:
        queryset = queryset.filter(
            work_order__work_order__icontains=work_order_query
        )
    if technician_query:
        name_filter = (
            Q(technician__First_Name__icontains=technician_query) |
            Q(technician__Last_Name__icontains=technician_query)
        )
        parts = technician_query.split()
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]
            name_filter |= (
                Q(technician__First_Name__icontains=first, technician__Last_Name__icontains=last) |
                Q(technician__First_Name__icontains=last, technician__Last_Name__icontains=first)
            )
        queryset = queryset.filter(name_filter)
        
    allowed_sorts = {
        'work_order': 'work_order__work_order',
        'start_date': 'start_date',
        'finish_date': 'finish_date',
        'total_time': 'total_time',
        'time_type': 'time_type',
    }
    
    if sort_by == 'technician':
        queryset = queryset.order_by('technician__First_Name', 'technician__Last_Name')
    else:
        queryset = queryset.order_by(allowed_sorts.get(sort_by, 'work_order'))
    filter_params = request.GET.copy()
    if 'sort' in filter_params:
        filter_params.pop('sort')
    filter_url = filter_params.urlencode()
    context = {
        'timesheets': queryset,
        'work_order_query': work_order_query,
        'technician_query': technician_query,
        'sort_by': sort_by,
        'filter_url': filter_url,
    }
    return render(request, 'timesheets/search_timesheets.html', context)