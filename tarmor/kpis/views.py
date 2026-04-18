from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import Count, Q, Sum, Count, Avg, F, ExpressionWrapper, fields
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from timesheets.models import Timesheet
from .models import FailureFrequency, MTBF
from failures.models import System, Component, FailureType, Action
from equipment.models import AssetType, EQ_Type, Equipment, MachineShiftStatus, ShiftReport
from work_orders.models import WorkOrder
from meters.models import MeterReading
import openpyxl
from openpyxl.styles import Font, PatternFill
from django.http import HttpResponse

def kpis(request):
    return render(request, 'kpis/kpis.html')

class TopFailuresView(ListView):
    model = WorkOrder
    template_name = 'kpis/top_failures.html'
    context_object_name = 'work_orders'

    def get_base_filtered_queryset(self):
        qs = WorkOrder.objects.select_related('equipment').filter(job_status__status_choice="Complete")
        start = self.request.GET.get('start_date')
        end = self.request.GET.get('end_date')
        asset_type = self.request.GET.get('asset_type')
        equip_num = self.request.GET.get('equip_num')
        equip_desc = self.request.GET.get('equip_desc')
        sys = self.request.GET.get('fc_system')
        comp = self.request.GET.get('fc_component')
        fail = self.request.GET.get('fc_failure_mode')
        action = self.request.GET.get('fc_action')
        
        if start and end:
            qs = qs.filter(date_closed__range=[start, end])
        if asset_type:
            qs = qs.filter(equipment__Asset_Type__icontains=asset_type)
        if equip_num:
            qs = qs.filter(equipment__Equipment_Number__icontains=equip_num)
        if equip_desc:
            qs = qs.filter(equipment__Equipment_Description__icontains=equip_desc)
        if sys:
            qs = qs.filter(fc_system__icontains=sys)
        if comp:
            qs = qs.filter(fc_component__icontains=comp)
        if fail:
            qs = qs.filter(fc_failure_mode__icontains=fail)
        if action:
            qs = qs.filter(fc_action__icontains=action)
        return qs
    
    def get_queryset(self):
        return self.get_base_filtered_queryset().order_by('-date_closed')[:5]
    
    def get_context_data(self, **kwargs):
        summary_qs = self.get_base_filtered_queryset()
        systems = summary_qs.exclude(fc_system__isnull=True).values('fc_system').annotate(total=Count('id')).order_by('-total')[:5]
        component = summary_qs.values('fc_component').annotate(total=Count('id')).order_by('-total')[:5]
        mode = summary_qs.values('fc_failure_mode').annotate(total=Count('id')).order_by('-total')[:5]
        action = summary_qs.values('fc_action').annotate(total=Count('id')).order_by('-total')[:5]
        context = super().get_context_data(**kwargs)
        
        for item in systems:
            item['obj'] = System.objects.filter(pk=item['fc_system']).first()
        context['system_counts'] = systems

        for item in component:
            item['obj'] = Component.objects.filter(pk=item['fc_component']).first()
        context['component_counts'] = component

        for item in mode:
            item['obj'] = FailureType.objects.filter(pk=item['fc_failure_mode']).first()
        context['mode_counts'] = mode
        
        for item in action:
            item['obj'] = Action.objects.filter(pk=item['fc_action']).first()
        context['action_counts'] = action

        context['filters'] = self.request.GET
        return context

def export_top_failures_excel(request):
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    asset_type = request.GET.get('asset_type')
    equip_num = request.GET.get('equip_num')
    sys = request.GET.get('fc_system')
    comp = request.GET.get('fc_component')
    fail = request.GET.get('fc_failure_mode')
    action = request.GET.get('fc_action')

    qs = WorkOrder.objects.select_related('equipment').all()

    if start and end:
        qs = qs.filter(date_closed__range=[start, end])
    if asset_type:
        qs = qs.filter(equipment__Asset_Type__icontains=asset_type)
    if equip_num:
        qs = qs.filter(equipment__Equipment_Number__icontains=equip_num)
    if sys:
        qs = qs.filter(fc_system__description__icontains=sys) 
    if comp:
        qs = qs.filter(fc_component__description__icontains=comp)
    if fail:
        qs = qs.filter(fc_failure_mode__description__icontains=fail)
    if action:
        qs = qs.filter(fc_action__description__icontains=action)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Work Order Failures"

    headers = [
        'WO #', 'Repair Description', 'Asset Type', 'Equip #', 'Equip Description', 
        'System', 'Component', 'Failure Mode', 'Action'
    ]
    ws.append(headers)

    for wo in qs:
        asset_type = str(wo.equipment.Asset_Type) if wo.equipment and wo.equipment.Asset_Type else ''
        equip_num = str(wo.equipment.Equipment_Number) if wo.equipment else ''
        equip_desc = str(wo.equipment.Equipment_Description) if wo.equipment else ''
        
        ws.append([
            wo.work_order,
            wo.repair_description,
            asset_type,
            equip_num,
            equip_desc,
            str(wo.fc_system), 
            str(wo.fc_component),
            str(wo.fc_failure_mode),
            str(wo.fc_action)
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Failure_Report.xlsx"'
    wb.save(response)
    return response

def failure_frequency_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    asset_type = request.GET.get('asset_type', '')
    eq_type = request.GET.get('equipment_type', '')
    eq_num = request.GET.get('equipment_number', '')
    sort_by = request.GET.get('sort', 'equipment_number')

    equipment_qs = Equipment.objects.all()
    if asset_type:
        equipment_qs = equipment_qs.filter(Asset_Type__name__icontains=asset_type)
    if eq_type:
        equipment_qs = equipment_qs.filter(Equipment_Type__Equipment_Type__icontains=eq_type)
    if eq_num:
        equipment_qs = equipment_qs.filter(Equipment_Number__icontains=eq_num)

    report_data = []

    for eq in equipment_qs:
        accumulated_hours = 0
        failures = 0
        
        if start_date and end_date:
            failures = WorkOrder.objects.filter(
                equipment=eq,
                work_type__work_type__in=["CF", "CP", "WTY"],
                date_created__range=[start_date, end_date]
            ).count()

            readings = MeterReading.objects.filter(
                Equipment_id=eq, 
                Date__range=[start_date, end_date]
            ).order_by('Date')
        
            if readings.exists():
                accumulated_hours = readings.last().Total_Meter_Value - readings.first().Total_Meter_Value
            
        report_data.append({
            'equipment_number': eq.Equipment_Number,
            'equipment_description': eq.Equipment_Description,
            'asset_type': eq.Asset_Type,
            'equipment_type': eq.Equipment_Type,
            'equipment_hours': accumulated_hours,
            'failure_count': failures,
            'frequency': round(failures / accumulated_hours, 4) if accumulated_hours > 0 else 0,
        })
            
    report_data = sorted(report_data, key=lambda x: x.get(sort_by, 0))
        
    asset_types = AssetType.objects.values_list('name', flat=True).distinct().order_by('name')
    equipment_types = EQ_Type.objects.values_list('Equipment_Type', flat=True).distinct().order_by('Equipment_Type')
    
    year = datetime.now().year
    monthly_data = (
        WorkOrder.objects.filter(
            equipment__in=equipment_qs,
            date_created__year=year,
            work_type__work_type__in=["CF", "CP", "WTY"]
        )
        .annotate(month=TruncMonth('date_created'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    labels, bar_data, line_data = [], [], []
    total_failures, months_processed = 0, 0

    for entry in monthly_data:
        labels.append(entry['month'].strftime('%b'))
        count = entry['count']
        bar_data.append(count)
        total_failures += count
        months_processed += 1
        line_data.append(round(total_failures / months_processed, 2))

    context = {
        'report_data': report_data,
        'labels': labels,
        'bar_data': bar_data,
        'line_data': line_data,
        'asset_types': asset_types,
        'equipment_types': equipment_types,
        'filters': request.GET,
        'sort_by': sort_by,
        'filter_url': request.GET.urlencode(),
    }
    return render(request, 'kpis/failure_frequency.html', context)

def failure_frequency_chart(request):
    year = datetime.now().year
    
    monthly_data = (
        WorkOrder.objects.filter(
            date_created__year=year,
            work_type__work_type__in=["CF", "CP", "WTY"]
        )
        .annotate(month=TruncMonth('date_created'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    labels = []
    bar_data = []
    line_data = []
    
    total_failures = 0
    months_processed = 0

    for entry in monthly_data:
        month_name = entry['month'].strftime('%b')
        count = entry['count']
        
        labels.append(month_name)
        bar_data.append(count)
        
        total_failures += count
        months_processed += 1
        line_data.append(round(total_failures / months_processed, 2))

    context = {
        'labels': labels,
        'bar_data': bar_data,
        'line_data': line_data,
        'current_year': year,
    }
    return render(request, 'kpis/failure_frequency.html', context)

def export_failure_frequency_excel(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    asset_type = request.GET.get('asset_type', '')
    eq_type = request.GET.get('equipment_type', '')
    eq_num = request.GET.get('equipment_number', '')

    equipment_qs = Equipment.objects.all()
    if asset_type:
        equipment_qs = equipment_qs.filter(Asset_Type__name__icontains=asset_type)
    if eq_type:
        equipment_qs = equipment_qs.filter(Equipment_Type__Equipment_Type__icontains=eq_type)
    if eq_num:
        equipment_qs = equipment_qs.filter(Equipment_Number__icontains=eq_num)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Failure Frequency Report"

    headers = [
        'Equip #', 'Equip Description', 'Asset Type', 'Equipment Type', 
        'Hours', 'Failures', 'Frequency'
    ]
    ws.append(headers)

    for eq in equipment_qs:
        accumulated_hours = 0
        failures = 0
        
        if start_date and end_date:
            # Re-run failure logic
            failures = WorkOrder.objects.filter(
                equipment=eq,
                work_type__work_type__in=["CF", "CP", "WTY"],
                date_created__range=[start_date, end_date]
            ).count()

            # Re-run meter logic
            readings = MeterReading.objects.filter(
                Equipment=eq, 
                Date__range=[start_date, end_date]
            ).order_by('Date')
            if readings.exists():
                accumulated_hours = readings.last().Total_Meter_Value - readings.first().Total_Meter_Value

        freq = round(failures / accumulated_hours, 4) if accumulated_hours > 0 else 0

        
        ws.append([
            eq.Equipment_Number,
            eq.Equipment_Description,
            str(eq.Asset_Type),
            str(eq.Equipment_Type),
            accumulated_hours,
            failures,
            freq
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Failure_Frequency.xlsx"'
    
    wb.save(response)
    return response

def mtbf_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    asset_type = request.GET.get('asset_type', '')
    eq_type = request.GET.get('equipment_type', '')
    eq_num = request.GET.get('equipment_number', '')
    year = datetime.now().year
    
    equipment_qs = Equipment.objects.all()
    if asset_type:
        equipment_qs = equipment_qs.filter(Asset_Type__name__icontains=asset_type)
    if eq_type:
        equipment_qs = equipment_qs.filter(Equipment_Type__Equipment_Type__icontains=eq_type)
    if eq_num:
        equipment_qs = equipment_qs.filter(Equipment_Number__icontains=eq_num)
        
    report_data = []
    
    for eq in equipment_qs:
        accumulated_hours = 0
        failures = 0
        
        if start_date and end_date:
            failures = WorkOrder.objects.filter(
                equipment=eq,
                work_type__work_type__in=["CF", "CP", "WTY"],
                date_created__range=[start_date, end_date]
            ).count()
        
            readings = MeterReading.objects.filter(
                Equipment=eq, 
                Date__range=[start_date, end_date]
            ).order_by('Date')
            
            if readings.exists():
                accumulated_hours = readings.last().Total_Meter_Value - readings.first().Total_Meter_Value
        
        mtbf = round(accumulated_hours / failures, 1) if failures > 0 else accumulated_hours
        
        report_data.append({
            'equipment_number': eq.Equipment_Number,
            'equipment_description': eq.Equipment_Description,
            'asset_type': eq.Asset_Type,
            'equipment_type': eq.Equipment_Type,
            'hours': accumulated_hours,
            'failures': failures,
            'mtbf': mtbf,
        })
        
    monthly_stats = (
        WorkOrder.objects.filter(
            equipment__in=equipment_qs,
            date_created__year=year,
            work_type__work_type__in=["CF", "CP", "WTY"]
        )
        .annotate(month=TruncMonth('date_created'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
          
    labels, bar_data, line_data = [], [], []
    total_failures, total_hours, months_processed = 0, 0, 0
    
    for entry in monthly_stats:
        labels.append(entry['month'].strftime('%b'))
        monthly_failures = entry['count']
        
        month_hours = 0
        current_month = entry['month'].month
        
        for eq in equipment_qs:
            m_readings = MeterReading.objects.filter(
                Equipment=eq, 
                Date__month=current_month,
                Date__year=year
            ).order_by('Date')
            
            if m_readings.exists():
                delta = m_readings.last().Total_Meter_Value - m_readings.first().Total_Meter_Value
                month_hours += delta
        
        if monthly_failures > 0:
            m_mtbf = round(month_hours / monthly_failures, 1)
        else:
            m_mtbf = month_hours
        bar_data.append(m_mtbf)
                
        total_failures += monthly_failures
        total_hours += month_hours
        
        if total_failures > 0:
            ytd_mtbf = round(total_hours / total_failures, 1)
        else:
            ytd_mtbf = total_hours
        line_data.append(ytd_mtbf)

    asset_types = AssetType.objects.values_list('name', flat=True).distinct().order_by('name')
    equipment_types = EQ_Type.objects.values_list('Equipment_Type', flat=True).distinct().order_by('Equipment_Type')

    context = {
        'report_data': report_data,
        'labels': labels,
        'bar_data': bar_data,
        'line_data': line_data,
        'current_year': year,
        'filters': request.GET,
        'asset_types': asset_types,
        'equipment_types': equipment_types,
    }

    return render(request, 'kpis/mtbf.html', context)

def export_mtbf_excel(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    asset_type = request.GET.get('asset_type', '')
    eq_type = request.GET.get('equipment_type', '')
    eq_num = request.GET.get('equipment_number', '')

    equipment_qs = Equipment.objects.all()
    if asset_type:
        equipment_qs = equipment_qs.filter(Asset_Type__name__icontains=asset_type)
    if eq_type:
        equipment_qs = equipment_qs.filter(Equipment_Type__Equipment_Type__icontains=eq_type)
    if eq_num:
        equipment_qs = equipment_qs.filter(Equipment_Number__icontains=eq_num)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "MTBF Report"

    headers = [
        'Equip #', 'Equip Description', 'Asset Type', 'Equipment Type', 
        'Hours', 'Failures', 'MTBF (Hours)'
    ]
    ws.append(headers)

    for eq in equipment_qs:
        accumulated_hours = 0
        failures = 0
        
        if start_date and end_date:
            failures = WorkOrder.objects.filter(
                equipment=eq,
                work_type__work_type__in=["CF", "CP", "WTY"],
                date_created__range=[start_date, end_date]
            ).count()

            readings = MeterReading.objects.filter(
                Equipment=eq, 
                Date__range=[start_date, end_date]
            ).order_by('Date')
            
            if readings.exists():
                accumulated_hours = readings.last().Total_Meter_Value - readings.first().Total_Meter_Value

        mtbf = round(accumulated_hours / failures, 4) if failures > 0 else accumulated_hours

        
        ws.append([
            eq.Equipment_Number,
            eq.Equipment_Description,
            str(eq.Asset_Type),
            str(eq.Equipment_Type),
            accumulated_hours,
            failures,
            mtbf
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="MTBF.xlsx"'
    
    wb.save(response)
    return response

def mttr_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    asset_type = request.GET.get('asset_type', '')
    eq_type = request.GET.get('equipment_type', '')
    eq_num = request.GET.get('equipment_number', '')
    year = datetime.now().year
    
    equipment_qs = Equipment.objects.all()
    if asset_type:
        equipment_qs = equipment_qs.filter(Asset_Type__name__icontains=asset_type)
    if eq_type:
        equipment_qs = equipment_qs.filter(Equipment_Type__Equipment_Type__icontains=eq_type)
    if eq_num:
        equipment_qs = equipment_qs.filter(Equipment_Number__icontains=eq_num)

    report_data = []
    
    for eq in equipment_qs:
        total_repair_hours = 0
        completed_repairs_count = 0

        work_orders = WorkOrder.objects.filter(
            equipment=eq,
            work_type__work_type__in=["CF", "CP", "WTY"],
            date_created__range=[start_date, end_date],
            date_closed__isnull=False
        )

        for wo in work_orders:
            if wo.machine_oos == 'Yes':
                duration = wo.date_closed - wo.date_created
                repair_time = duration.total_seconds() / 3600
            else:
                repair_time = Timesheet.objects.filter(work_order=wo).aggregate(
                    total=Sum('total_time'))['total'] or 0
            
            total_repair_hours += repair_time
            completed_repairs_count += 1

        mttr = round(total_repair_hours / completed_repairs_count, 1) if completed_repairs_count > 0 else 0

        report_data.append({
            'equipment_number': eq.Equipment_Number,
            'equipment_description': eq.Equipment_Description,
            'asset_type': eq.Asset_Type,
            'equipment_type': eq.Equipment_Type,
            'total_repair_hours': total_repair_hours,
            'repair_count': completed_repairs_count,
            'mttr': mttr,
        })

    monthly_stats = (
        WorkOrder.objects.filter(
            equipment__in=equipment_qs,
            date_created__year=year,
            work_type__work_type__in=["CF", "CP", "WTY"],
            date_closed__isnull=False
        )
        .annotate(month=TruncMonth('date_created'))
        .order_by('month')
    )
    
    buckets = {}
    
    for wo in monthly_stats:
        m_key = wo.month.strftime('%b')
        if m_key not in buckets:
            buckets[m_key] = {'total_hrs': 0, 'count': 0}
        
        if wo.machine_oos == 'Yes':
            diff = wo.date_closed - wo.date_created
            repair_time = diff.total_seconds() / 3600
        else:
            repair_time = Timesheet.objects.filter(work_order=wo).aggregate(
                total=Sum('total_time'))['total'] or 0
        
        buckets[m_key]['total_hrs'] += repair_time
        buckets[m_key]['count'] += 1
        
    labels = []
    bar_data = [] 
    line_data = [] 
    
    cumulative_hrs = 0
    cumulative_count = 0
    
    for month_name, data in buckets.items():
        labels.append(month_name)
        
        m_avg = round(data['total_hrs'] / data['count'], 1) if data['count'] > 0 else 0
        bar_data.append(m_avg)
        
        cumulative_hrs += data['total_hrs']
        cumulative_count += data['count']
        ytd_avg = round(cumulative_hrs / cumulative_count, 1) if cumulative_count > 0 else 0
        line_data.append(ytd_avg)
        asset_types = AssetType.objects.values_list('name', flat=True).distinct().order_by('name')
        equipment_types = EQ_Type.objects.values_list('Equipment_Type', flat=True).distinct().order_by('Equipment_Type')
    
    context = {
        'report_data': report_data,
        'labels': labels,
        'bar_data': bar_data,
        'line_data': line_data,
        'current_year': year,
        'filters': request.GET,
        'mttr': mttr,
        'asset_types': asset_types,
        'equipment_types': equipment_types,
    }
    
    return render(request, 'kpis/mttr.html', context)

def export_mttr_excel(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    asset_type = request.GET.get('asset_type', '')
    eq_type = request.GET.get('equipment_type', '')
    eq_num = request.GET.get('equipment_number', '')

    equipment_qs = Equipment.objects.all()
    if asset_type:
        equipment_qs = equipment_qs.filter(Asset_Type__name__icontains=asset_type)
    if eq_type:
        equipment_qs = equipment_qs.filter(Equipment_Type__Equipment_Type__icontains=eq_type)
    if eq_num:
        equipment_qs = equipment_qs.filter(Equipment_Number__icontains=eq_num)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "MTTR Report"

    headers = [
        'Equip #', 'Description', 'Asset Type', 'Equipment Type', 
        'Repair Count', 'Total Repair Hours', 'MTTR (Hours)'
    ]
    ws.append(headers)

    for eq in equipment_qs:
        total_repair_hours = 0
        completed_count = 0

        if start_date and end_date:
            work_orders = WorkOrder.objects.filter(
                equipment=eq,
                work_type__work_type__in=["CF", "CP", "WTY"],
                date_created__range=[start_date, end_date],
                date_closed__isnull=False
            )

            for wo in work_orders:
                if wo.machine_oos == 'yes':
                    duration = wo.date_closed - wo.date_created
                    repair_time = duration.total_seconds() / 3600
                else:
                    repair_time = Timesheet.objects.filter(work_order=wo).aggregate(
                        total=Sum('total_time'))['total'] or 0
                
                total_repair_hours += repair_time
                completed_count += 1

        mttr = round(total_repair_hours / completed_count, 1) if completed_count > 0 else 0

        ws.append([
            eq.Equipment_Number,
            eq.Equipment_Description,
            str(eq.Asset_Type),
            str(eq.Equipment_Type),
            completed_count,
            round(total_repair_hours, 1),
            mttr
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="MTTR_Report.xlsx"'
    
    wb.save(response)
    return response

def availability_utilisation_report(request):
    # 1. Setup Filters (Replicated from MTTR)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    asset_type = request.GET.get('asset_type', '')
    eq_type = request.GET.get('equipment_type', '')
    eq_num = request.GET.get('equipment_number', '')
    year = datetime.now().year

    equipment_qs = Equipment.objects.all()
    if asset_type:
        equipment_qs = equipment_qs.filter(Asset_Type__name__icontains=asset_type)
    if eq_type:
        equipment_qs = equipment_qs.filter(Equipment_Type__Equipment_Type__icontains=eq_type)
    if eq_num:
        equipment_qs = equipment_qs.filter(Equipment_Number__icontains=eq_num)

    date_format = "%Y-%m-%d"
    try:
        delta = datetime.strptime(end_date, date_format) - datetime.strptime(start_date, date_format)
        total_days = max(delta.days + 1, 1)
    except:
        total_days = 1

    total_potential_hours = total_days * 24

    report_data = []
    for eq in equipment_qs:
        stats = MachineShiftStatus.objects.filter(
            equipment=eq,
            report__date__range=[start_date, end_date]
        ).aggregate(
            sum_down=Sum('total_down'),
            sum_worked=Sum('total_worked'),
            sum_available=Sum('available')
        )
        
        total_down = stats['sum_down'] or 0
        worked_hrs = stats['sum_worked'] or 0
        available = stats['sum_available'] or 0
                
        availability_pct = round((available / total_potential_hours) * 100, 1)
        utilisation_pct = round((worked_hrs / total_potential_hours) * 100, 1)

        report_data.append({
            'equipment_number': eq.Equipment_Number,
            'equipment_description': eq.Equipment_Description,
            'asset_type': eq.Asset_Type,
            'equipment_type': eq.Equipment_Type,
            'total_down': total_down,
            'available': max(availability_pct, 0),
            'total_worked': utilisation_pct,
        })

    monthly_stats = MachineShiftStatus.objects.filter(
        equipment__in=equipment_qs,
        report__date__year=datetime.now().year
    ).annotate(
        month=TruncMonth('report__date')
    ).values('month').annotate(
        m_down=Sum('total_down'),
        m_worked=Sum('total_worked'),
        m_available=Sum('available')
    ).order_by('month')

    labels = []
    avail_chart_data = []  # Bars
    util_chart_data = []   # Lines
    
    for entry in monthly_stats:
        m_date = entry['month']
        labels.append(m_date.strftime('%b'))
        
        import calendar
        days_in_month = calendar.monthrange(m_date.year, m_date.month)[1]
        m_potential_hrs = equipment_qs.count() * days_in_month * 24
        
        m_avail_val = entry['m_available'] or 0
        m_worked_val = entry['m_worked'] or 0
            
        avail_chart_data.append(round((m_avail_val / m_potential_hrs) * 100, 1) if m_potential_hrs > 0 else 0)
        util_chart_data.append(round((m_worked_val / m_potential_hrs) * 100, 1) if m_potential_hrs > 0 else 0)

    context = {
        'report_data': report_data,
        'labels': labels,
        'avail_chart_data': avail_chart_data, # Bar
        'util_chart_data': util_chart_data,   # Line
        'filters': request.GET,
        'asset_types': AssetType.objects.all(),
        'equipment_types': EQ_Type.objects.all(),
    }
    
    return render(request, 'kpis/availability.html', context)

def export_au_excel(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    asset_type = request.GET.get('asset_type', '')
    eq_type = request.GET.get('equipment_type', '')
    eq_num = request.GET.get('equipment_number', '')

    equipment_qs = Equipment.objects.all()
    if asset_type:
        equipment_qs = equipment_qs.filter(Asset_Type__name__icontains=asset_type)
    if eq_type:
        equipment_qs = equipment_qs.filter(Equipment_Type__Equipment_Type__icontains=eq_type)
    if eq_num:
        equipment_qs = equipment_qs.filter(Equipment_Number__icontains=eq_num)
        
    try:
        delta = datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")
        total_potential_hours = max((delta.days + 1) * 24, 1)
    except:
        total_potential_hours = 24
        
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "A&U Report"

    headers = ['Equipment #', 'Description', 'Asset Type', 'Downtime (Hrs)', 'Availability %', 'Utilisation %']
    header_fill = PatternFill(start_color="36A2EB", end_color="36A2EB", fill_type="solid")
    
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill

    for eq in equipment_qs:
        stats = MachineShiftStatus.objects.filter(
            equipment=eq,
            report__date__range=[start_date, end_date]
        ).aggregate(
            sum_down=Sum('total_down'),
            sum_worked=Sum('total_worked'),
            sum_available=Sum('available')
        )

        down = stats['sum_down'] or 0
        worked = stats['sum_worked'] or 0
        available_hrs = stats['sum_available'] or 0
        
        avail_pct = round((available_hrs / total_potential_hours) * 100, 1) if total_potential_hours > 0 else 0
        util_pct = round((worked / total_potential_hours) * 100, 1) if total_potential_hours > 0 else 0

        ws.append([
            eq.Equipment_Number,
            eq.Equipment_Description,
            str(eq.Asset_Type),
            down,
            f"{avail_pct}%",
            f"{util_pct}%"
        ])
        
    for col in ws.columns:
        column_letter = col[0].column_letter
        ws.column_dimensions[column_letter].width = 20

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=AU_Report_{datetime.now().strftime("%Y%m%d")}.xlsx'
    wb.save(response)
    return response