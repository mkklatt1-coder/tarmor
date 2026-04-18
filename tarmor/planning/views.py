from django.contrib import messages
from django.forms.models import inlineformset_factory
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
import openpyxl
from .forms import (
    QualityMaintenanceCreateForm,
    QualityMaintenanceEditForm,
    QualityMaintenanceStepFormSet,
    QualityMaintenanceSearchForm,
    QualityMaintenanceEditLookupForm,
    QualityMaintenanceStepForm,
    QualityMaintenanceStep
)
from .models import QualityMaintenance, QualityMaintenanceInstance
from work_orders.models import WorkOrder
from .services import evaluate_qm_for_work_order_creation
from django.utils import timezone
from datetime import timedelta

def planning(request):
    return render(request, 'planning/planning.html')

def create_qm(request):
    StepFormSetClass = inlineformset_factory(
        QualityMaintenance,
        QualityMaintenanceStep,
        form=QualityMaintenanceStepForm,
        extra=2,
        can_delete=True
    )
    if request.method == 'POST':
        form = QualityMaintenanceCreateForm(request.POST, request.FILES, instance=qm)
        formset = StepFormSetClass(request.POST)
        form_valid = form.is_valid()
        formset_valid = formset.is_valid()
        if form_valid:
            step_type = form.cleaned_data.get('step_type')
            qm_type = form.cleaned_data.get('qm_type')
            if step_type == 'MULTI':
                valid_step_forms = []
                calendar_groups = set()
                for f in formset.forms:
                    cleaned = getattr(f, 'cleaned_data', None)
                    if cleaned and not cleaned.get('DELETE', False) and cleaned.get('interval_value'):
                        valid_step_forms.append(f)
                        if qm_type == 'CALENDAR':
                            if not cleaned.get('interval_unit'):
                                form.add_error(
                                    None,
                                    f'Sequence step {cleaned.get("step_order") or ""} requires an interval unit for calendar QM.'
                                )
                            else:
                                unit = cleaned.get('interval_unit')
                                if unit in ['DAY', 'WEEK']:
                                    calendar_groups.add('DAY_BASED')
                                elif unit in ['MONTH', 'YEAR']:
                                    calendar_groups.add('MONTH_BASED')
                        elif qm_type == 'METER':
                            if cleaned.get('interval_unit'):
                                form.add_error(
                                    None,
                                    'Meter QM sequence steps should not have a calendar interval unit.'
                                )
                if not valid_step_forms:
                    form.add_error(None, 'At least one sequence step is required for multi-step QM.')
                if qm_type == 'CALENDAR' and len(calendar_groups) > 1:
                    form.add_error(
                        None,
                        'Calendar multi-step QM cannot mix day/week intervals with month/year intervals.'
                    )
        if form_valid and formset_valid and not form.errors:
            with transaction.atomic():
                qm = form.save()
                formset.instance = qm
                formset.save()
            messages.success(request, f'QM {qm.qm_number} created successfully.')
            return redirect('planning:edit_qm_record', pk=qm.pk)
    else:
        form = QualityMaintenanceCreateForm()
        formset = StepFormSetClass()
    return render(request, 'planning/create_qm.html', {
        'qmform': form,
        'step_formset': formset,
        'preview_number': QualityMaintenance.get_next_number()
    })
    
def edit_qm(request):
    if request.method == 'POST':
        form = QualityMaintenanceEditLookupForm(request.POST)
        if form.is_valid():
            qm = form.cleaned_data['qm_number']
            return redirect('planning:edit_qm_record', pk=qm.pk)
    else:
        form = QualityMaintenanceEditLookupForm()
    return render(request, 'planning/edit_qm.html', {
        'lookup_form': form,
    })
    
def edit_qm_record(request, pk):
    qm = get_object_or_404(QualityMaintenance, pk=pk) if pk else None
    StepFormSetClass = inlineformset_factory(
        QualityMaintenance,
        QualityMaintenanceStep,
        form=QualityMaintenanceStepForm,
        extra=0,
        can_delete=True
    )
    if request.method == 'POST':
        form = QualityMaintenanceEditForm(request.POST, request.FILES, instance=qm)
        formset = StepFormSetClass(request.POST, request.FILES, instance=qm)
        form_valid = form.is_valid()
        formset_valid = formset.is_valid()
        if form_valid:
            step_type = form.cleaned_data.get('step_type')
            qm_type = form.cleaned_data.get('qm_type')
            if step_type == 'MULTI':
                valid_step_forms = []
                calendar_groups = set()
                for f in formset.forms:
                    cleaned = getattr(f, 'cleaned_data', None)
                    if cleaned and not cleaned.get('DELETE', False) and cleaned.get('interval_value'):
                        valid_step_forms.append(f)
                        if qm_type == 'CALENDAR':
                            if not cleaned.get('interval_unit'):
                                form.add_error(
                                    None,
                                    f'Sequence step {cleaned.get("step_order") or ""} requires an interval unit for calendar QM.'
                                )
                            else:
                                unit = cleaned.get('interval_unit')
                                if unit in ['DAY', 'WEEK']:
                                    calendar_groups.add('DAY_BASED')
                                elif unit in ['MONTH', 'YEAR']:
                                    calendar_groups.add('MONTH_BASED')
                        elif qm_type == 'METER':
                            if cleaned.get('interval_unit'):
                                form.add_error(
                                    None,
                                    'Meter QM sequence steps should not have a calendar interval unit.'
                                )
                if not valid_step_forms:
                    form.add_error(None, 'At least one sequence step is required for multi-step QM.')
                if qm_type == 'CALENDAR' and len(calendar_groups) > 1:
                    form.add_error(
                        None,
                        'Calendar multi-step QM cannot mix day/week intervals with month/year intervals.'
                    )
        if form_valid and formset_valid and not form.errors:
            with transaction.atomic():
                qm = form.save()
                formset.save()
                if 'save_exit' in request.POST:
                    messages.success(request, f'QM {qm.qm_number} updated successfully.')
                    next_url = request.GET.get('next')
                    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                        return redirect(next_url)
                    else:
                        return redirect('planning:planning')
                messages.success(request, f'QM {qm.qm_number} updated successfully.')
                return redirect('planning:edit_qm_record', pk=qm.pk)
    else:
        form = QualityMaintenanceEditForm(instance=qm)
        formset = StepFormSetClass(instance=qm)
    forecast = qm.get_next_due()
    trigger_date = qm.get_work_order_trigger_date()
    avg_daily_usage = qm.get_average_daily_usage() if qm.qm_type == 'METER' else None
    current_meter = qm.get_current_meter() if qm.qm_type == 'METER' else None
    return render(request, 'planning/edit_qm_record.html', {
        'qmform': form,
        'step_formset': formset,
        'qm': qm,
        'forecast': forecast,
        'trigger_date': trigger_date,
        'avg_daily_usage': avg_daily_usage,
        'current_meter': current_meter,
    })
    
def search_qm(request):
    form = QualityMaintenanceSearchForm(request.GET or None)
    results = QualityMaintenance.objects.select_related('equipment', 'meter_type').all()
    if form.is_valid():
        qm_number = form.cleaned_data.get('qm_number')
        equipment_number = form.cleaned_data.get('equipment_number')
        description = form.cleaned_data.get('description')
        qm_type = form.cleaned_data.get('qm_type')
        step_type = form.cleaned_data.get('step_type')
        active = form.cleaned_data.get('active')
        if qm_number:
            results = results.filter(qm_number__icontains=qm_number)
        if equipment_number:
            results = results.filter(equipment__Equipment_Number__icontains=equipment_number)
        if description:
            results = results.filter(description__icontains=description)
        if qm_type:
            results = results.filter(qm_type=qm_type)
        if step_type:
            results = results.filter(step_type=step_type)
        if active is not None:
            results = results.filter(active=active)
    enriched_results = []
    for qm in results:
        forecast = qm.get_next_due()
        enriched_results.append({
            'qm': qm,
            'next_due_date': forecast.get('next_due_date'),
            'next_due_meter': forecast.get('next_due_meter'),
            'step': forecast.get('step'),
        })
    return render(request, 'planning/search_qm.html', {
        'search_form': form,
        'results': enriched_results,
    })
    
def search_plan_orders(request):
    work_orders = WorkOrder.objects.select_related('equipment', 'job_status').filter(
        job_status__status_choice='Planning')
    
    sort_by = request.GET.get('sort', '-date_created')
    work_orders = work_orders.order_by(sort_by)

    return render(request, 'planning/search_plan_orders.html', {
        'work_orders': work_orders,
        'job_status': 'Planning',
    })
    
def export_plan_wos_excel(request):
    work_orders = WorkOrder.objects.select_related('equipment', 'job_status').filter(
        job_status__status_choice='planning')
    
    sort_by = request.GET.get('sort', '-date_created')
    work_orders = work_orders.order_by(sort_by)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Work Orders In Planning"

    ws.append(['Work Order', 'Eq Num', 'Eq Desc', 'Status'])

    for wo in work_orders:
        ws.append([
            str(wo.work_order), 
            wo.equipment.Equipment_Number,
            wo.equipment.Equipment_Description,
            str(wo.job_status)
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Plan_Work_Export.xlsx"'
    wb.save(response)
    return response

def create_qm_work_order_now(request, pk):
    qm = get_object_or_404(QualityMaintenance, pk=pk)
    work_order, created, message = evaluate_qm_for_work_order_creation(qm)
    
    if created:
        messages.success(request, message)
    else:
        messages.warning(request, message)
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('planning:edit_qm_record', pk=qm.pk)

def forecast(request):
    today = timezone.localdate()
    next_week = today + timedelta(days=7)
    
    forecast_items = QualityMaintenanceInstance.objects.filter(
        due_date__range=[today, next_week]
    ).select_related('qm', 'work_order', 'step')

    if request.method == "POST" and 'run_forecast' in request.POST:
            all_active_qms = QualityMaintenance.objects.filter(active=True)
            count = 0
            for qm in all_active_qms:
                wo, created, msg = evaluate_qm_for_work_order_creation(qm)
                if created:
                    count += 1
            return redirect('planning:forecast')

    return render(request, 'planning/forecast.html', {
        'forecast_items': forecast_items,
        'today': today,
        'next_week': next_week
    })