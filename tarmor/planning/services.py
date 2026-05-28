from django.db import transaction
from django.utils import timezone
from .models import QualityMaintenanceInstance, QualityMaintenanceDocument, QualityMaintenancePlan, QualityMaintenanceDocumentStep
from work_orders.models import WorkOrder, StatusChoices, WorkType
from datetime import timedelta
now = timezone.now()

def get_or_create_default_work_order_status():
    status, _ = StatusChoices.objects.get_or_create(
        status_choice='Open'
    )
    return status

def get_or_create_default_work_type():
    work_type, _ = WorkType.objects.get_or_create(
        work_type='PM',
        defaults={'work_description': 'Preventive Maintenance'}
    )
    return work_type

def build_qm_work_order_description(plan, forecast):
    doc = plan.document
    step = forecast.get('step')
    
    base = f'QM {doc.qm_number}'
    if doc.qm_type == 'CALENDAR':
        if step and step.interval_unit:
            return f'{base} {step.interval_value} {step.get_interval_unit_display()} service due'
    else: # METER
        meter_name = str(plan.meter_type) if plan.meter_type else 'meter'
        if step:
            return f'{base} {step.interval_value} {meter_name} service due'
    return f'{base} service due'

def evaluate_plan_for_forecast(plan):
    if not plan.active:
        return None
        
    forecast = plan.get_next_due()
    due_date = forecast.get('next_due_date')
    trigger_date = plan.get_work_order_trigger_date()
    
    if not due_date or not trigger_date:
        return None

    today = timezone.localdate()
    limit = today + timedelta(days=14)

    if trigger_date <= limit:
        existing = QualityMaintenanceInstance.objects.filter(
            plan=plan, 
            due_date=due_date, 
            due_meter=forecast.get('next_due_meter')
        ).exists()
        
        if not existing:
            return {
                'plan': plan,
                'due_date': due_date,
                'due_meter': forecast.get('next_due_meter'),
                'trigger_date': trigger_date,
                'description': build_qm_work_order_description(plan, forecast),
                'step_label': forecast.get('step').step_label if forecast.get('step') else "Scheduled Maintenance"
            }
    return None

def find_existing_qm_instance(plan, forecast):
    qs = plan.instances.all()
    due_date = forecast.get('next_due_date')
    due_meter = forecast.get('next_due_meter')
    step = forecast.get('step')

    if due_date is not None:
        qs = qs.filter(due_date=due_date)
    if due_meter is not None:
        qs = qs.filter(due_meter=due_meter)
    if step is not None:
        qs = qs.filter(step=step)
    return qs.first()

def evaluate_qm_for_work_order_creation(plan):
    if not plan.active:
        return None, False, 'Plan is inactive.'
    
    forecast = plan.get_next_due()
    due_date = forecast.get('next_due_date')
    due_meter = forecast.get('next_due_meter')
    step = forecast.get('step')
    trigger_date = plan.get_work_order_trigger_date()
    checklist_to_attach = None
    parts_list_to_attach = None
    hrs_to_attach = None
    doc = plan.document

    if step:
        checklist_to_attach = step.step_checklist
        parts_list_to_attach = step.step_parts_list
        hrs_to_attach = step.est_work_hours
    else: 
        checklist_to_attach = doc.single_interval_checklist
        parts_list_to_attach = doc.single_interval_parts_list
        hrs_to_attach = doc.est_work_hours
        
    step_label = step.step_label if step else "Scheduled Maintenance"
    original_description = build_qm_work_order_description(plan, forecast)
    
    if due_date is None and due_meter is None:
        return None, False, 'Plan has no calculable next due.'
    
    if trigger_date is None:
        return None, False, 'Plan has no calculable trigger date.'
    
    today = timezone.localdate()
    if today < trigger_date:
        return None, False, f'Plan not yet in WO trigger window. Trigger date is {trigger_date}.'
    existing_instance = find_existing_qm_instance(plan, forecast)
    
    if existing_instance:
        if getattr(existing_instance, 'work_order', None):
            return existing_instance.work_order, False, 'Work order already exists for this QM due event.'
        
    status = get_or_create_default_work_order_status()
    work_type = get_or_create_default_work_type()
    
    with transaction.atomic():
        work_order = WorkOrder.objects.create(
            equipment=plan.equipment,
            job_status=status,
            work_type=work_type,
            troubleshoot_description=step_label,
            repair_description=step_label, 
            repair_extended_description=original_description,
            machine_oos="No",
            meter=plan.meter_type,
            attached_checklist=checklist_to_attach,
            attached_parts_list=parts_list_to_attach, 
            est_work_hours=hrs_to_attach,
            equipment_location=getattr(plan.equipment, 'Responsible_Garage', None),
            plan_start_date=timezone.make_aware(
                timezone.datetime.combine(due_date, timezone.datetime.min.time())
            ) if due_date else None,
        )
        if existing_instance:
            instance = existing_instance
            instance.status = 'TRIGGERED'
            instance.work_order = work_order
            if due_date is not None:
                instance.due_date = due_date
            if due_meter is not None:
                instance.due_meter = due_meter
            if step is not None:
                instance.step = step
            instance.save()
        else:
            instance = QualityMaintenanceInstance.objects.create(
                plan=plan,
                step=step,
                due_date=due_date,
                due_meter=due_meter,
                status='TRIGGERED',
                work_order=work_order,
            )
    return work_order, True, f'Work order {work_order.work_order} created.'

def evaluate_all_qms_for_work_orders():
    results = []
    qms = QualityMaintenancePlan.objects.filter(active=True).select_related(
        'equipment',
        'meter_type',
    )
    for qm in qms:
        work_order, created, message = evaluate_qm_for_work_order_creation(qm)
        results.append({
            'qm': qm,
            'work_order': work_order,
            'created': created,
            'message': message,
        })
    return results
