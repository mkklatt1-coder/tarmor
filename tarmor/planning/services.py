from django.db import transaction
from django.utils import timezone
from .models import QualityMaintenanceInstance, QualityMaintenance
from work_orders.models import WorkOrder, StatusChoices, WorkType

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

def build_qm_work_order_description(qm, forecast):
    if qm.qm_type == 'CALENDAR':
        if forecast.get('step'):
            step = forecast['step']
            if step.interval_unit:
                return f'QM {qm.qm_number} {step.interval_value} {step.get_interval_unit_display()} service due'
            return f'QM {qm.qm_number} service due'
        return f'QM {qm.qm_number} service due'
    if qm.qm_type == 'METER':
        if forecast.get('step'):
            step = forecast['step']
            meter_name = str(qm.meter_type) if qm.meter_type else 'meter'
            return f'QM {qm.qm_number} {step.interval_value} {meter_name} service due'
        return f'QM {qm.qm_number} service due'
    return f'QM {qm.qm_number} service due'

def find_existing_qm_instance(qm, forecast):
    qs = qm.instances.all()
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

def evaluate_qm_for_work_order_creation(qm):
    """
    Creates a work order if:
    - QM is active
    - next due exists
    - trigger date is today or earlier
    - no WO already exists for that due event
    """
    if not qm.active:
        return None, False, 'QM is inactive.'
    forecast = qm.get_next_due()
    due_date = forecast.get('next_due_date')
    due_meter = forecast.get('next_due_meter')
    step = forecast.get('step')
    trigger_date = qm.get_work_order_trigger_date()
    checklist_to_attach = None
    hrs_to_attach = None
    
    if step and step.step_checklist:
        checklist_to_attach = step.step_checklist
    elif qm.single_interval_checklist:
        checklist_to_attach = qm.single_interval_checklist

    if step and step.est_work_hours:
        hrs_to_attach = step.est_work_hours
    elif qm.est_work_hours:
        hrs_to_attach = qm.est_work_hours
        
    step_label = step.step_label if step else "Scheduled Maintenance"
    original_description = build_qm_work_order_description(qm, forecast)
    
    if due_date is None and due_meter is None:
        return None, False, 'QM has no calculable next due.'
    
    if trigger_date is None:
        return None, False, 'QM has no calculable trigger date.'
    
    today = timezone.localdate()
    if today < trigger_date:
        return None, False, f'QM not yet in WO trigger window. Trigger date is {trigger_date}.'
    existing_instance = find_existing_qm_instance(qm, forecast)
    
    if existing_instance:
        if getattr(existing_instance, 'work_order', None):
            return existing_instance.work_order, False, 'Work order already exists for this QM due event.'
        
    status = get_or_create_default_work_order_status()
    work_type = get_or_create_default_work_type()
    
    with transaction.atomic():
        work_order = WorkOrder.objects.create(
            equipment=qm.equipment,
            job_status=status,
            work_type=work_type,
            troubleshoot_description=step_label,
            repair_description=step_label, 
            repair_extended_description=original_description,
            machine_oos="No",
            meter=qm.meter_type,
            attached_checklist=checklist_to_attach,
            est_work_hours=hrs_to_attach,
            equipment_location=getattr(qm.equipment, 'Responsible_Garage', None),
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
                qm=qm,
                step=step,
                due_date=due_date,
                due_meter=due_meter,
                status='TRIGGERED',
                work_order=work_order,
            )
    return work_order, True, f'Work order {work_order.work_order} created.'

def evaluate_all_qms_for_work_orders():
    results = []
    qms = QualityMaintenance.objects.filter(active=True).select_related(
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