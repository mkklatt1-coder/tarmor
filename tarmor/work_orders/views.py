from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Q
from django.conf import settings
from .forms import WorkOrderAddForm, WorkOrderEditForm
from .models import WorkOrder
from equipment.models import Component, Equipment
import openpyxl, pdfrw, io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pathlib import Path
from planning.models import QualityMaintenance

def work_orders(request):
    return render(request, 'work_orders/work_orders.html')

def add_work_order(request):
    all_equipment = Equipment.objects.all().values_list('Equipment_Number', flat=True)
    if request.method == 'POST':
        workorderform = WorkOrderAddForm(request.POST, request.FILES)
        if workorderform.is_valid():
            work_order = workorderform.save()
            messages.success(request, 'Work order created successfully.')
            if 'save_continue' in request.POST:
                return redirect('work_orders:edit_work_order', pk=work_order.pk)
            return redirect('work_orders:work_orders')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        workorderform = WorkOrderAddForm()
    return render(request, 'work_orders/add_work_order.html', {
        'all_equipment': all_equipment,
        'workorderform': workorderform,
        'preview_work_order': WorkOrder.generate_work_order_number(),
    })
    
def edit_work_order(request, pk=None):
    
    orders=WorkOrder.objects.all().values_list('work_order', flat=True)
    query = request.GET.get('q')
    
    if query:
        target_order = WorkOrder.objects.filter(work_order=query).first()
        if target_order:
            return redirect('work_orders:edit_work_order', pk=target_order.pk)
        else:
            pass
        
    work_order_obj = None 
    components = None
           
    if pk:
        work_order_obj = get_object_or_404(WorkOrder, pk=pk)
        components = Component.objects.filter(Equipment=work_order_obj.equipment)
        
    if request.method == 'POST':
        workorderform = WorkOrderEditForm(request.POST, request.FILES, instance=work_order_obj)
        if workorderform.is_valid():
            workorderform.save()
            if request.POST.get('save_cont') == 'true':
                messages.success(request, 'Work order updated successfully.')
                next_url = request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
            messages.success(request, 'Work order updated successfully.')
            return redirect('work_orders:work_orders')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        workorderform = WorkOrderEditForm(instance=work_order_obj)

    return render(request, 'work_orders/edit_work_order.html', {
        'orders': orders,
        'workorderform': workorderform,
        'work_order_obj': work_order_obj,
        'components': components,
    })
    
def equipment_lookup(request):
    query = request.GET.get('q', '').strip()
    field = request.GET.get('field', 'all').strip()
    results = []
    if query:
        qs = Equipment.objects.all()
        if field == 'number':
            qs = qs.filter(Equipment_Number__icontains=query)
        elif field == 'description':
            qs = qs.filter(Equipment_Description__icontains=query)
        else:
            qs = qs.filter(
                Q(Equipment_Number__icontains=query) |
                Q(Equipment_Description__icontains=query)
            )
        qs = qs.order_by('Equipment_Number')[:20]
        results = [
            {
                'id': eq.pk,
                'equipment_number': eq.Equipment_Number,
                'equipment_description': eq.Equipment_Description,
            }
            for eq in qs
        ]
    return JsonResponse({'results': results})

def search_work_orders(request):
    work_orders = WorkOrder.objects.all()
    
    wo_num = request.GET.get('work_order') or ''
    eq_num = request.GET.get('equipment_number') or ''
    eq_desc = request.GET.get('equipment_description') or ''
    status = request.GET.get('job_status') or ''
    
    work_orders = WorkOrder.objects.select_related('equipment', 'job_status').all()
    
    if wo_num:
        work_orders = work_orders.filter(work_order__icontains=wo_num)
    if eq_num:
        work_orders = work_orders.filter(equipment__Equipment_Number__icontains=eq_num)
    if eq_desc:
        work_orders = work_orders.filter(equipment__Equipment_Description__icontains=eq_desc)
    if status:
        work_orders = work_orders.filter(job_status__status_choice__icontains=status)
        
    sort_by = request.GET.get('sort', '-date_created')
    work_orders = work_orders.order_by(sort_by)

    return render(request, 'work_orders/search_work_orders.html', {
        'work_orders': work_orders,
        'work_order': wo_num,
        'equipment_number': eq_num,
        'equipment_description': eq_desc,
        'job_status': status,
    })
    
def export_wos_excel(request):
    
    work_orders = WorkOrder.objects.select_related('equipment', 'job_status').all()
    
    wo_num = request.GET.get('work_order', '')
    eq_num = request.GET.get('equipment_number', '')
    eq_desc = request.GET.get('equipment_description', '')
    status = request.GET.get('job_status', '')
    
    if wo_num:
        work_orders = work_orders.filter(work_order__icontains=wo_num)
    if eq_num:
        work_orders = work_orders.filter(equipment__Equipment_Number__icontains=eq_num)
    if eq_desc:
        work_orders = work_orders.filter(equipment__Equipment_Description__icontains=eq_desc)
    if status:
        work_orders = work_orders.filter(job_status__status_choice__icontains=status)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Work Orders"

    ws.append(['Work Order', 'Eq Num', 'Eq Desc', 'Status'])

    for wo in work_orders:
        ws.append([
            str(wo.work_order), 
            wo.equipment.Equipment_Number,
            wo.equipment.Equipment_Description,
            str(wo.job_status)
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Work_Order_Export.xlsx"'
    wb.save(response)
    return response

def fill_pdf(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk)
        
    data_dict = {
        'work_order': str(wo.work_order),
        'equipment_number': str(wo.equipment.Equipment_Number),
        'equipment_description': str(wo.equipment.Equipment_Description or ""),
        'work_type': str(wo.work_type.work_type) if wo.work_type else "",
        'priority': str(wo.priority or ""),
        'machine_oos': str(wo.machine_oos or ""),
        'hours': str(wo.hours or ""),
        'meter': str(wo.meter or ""),
        'job_status': str(wo.job_status.status_choice) if wo.job_status else "",
        'date_created': wo.date_created.strftime('%Y-%m-%d %H:%M') if wo.date_created else "",
        'troubleshoot_description': str(wo.troubleshoot_description),
        'ts_extended_description': str(wo.ts_extended_description or ""),
        'equipment_location': str(wo.equipment_location or ""),
        'ts_service_report': str(wo.ts_service_report or ""),
        'plan_start_date': wo.plan_start_date.strftime('%Y-%m-%d') if wo.plan_start_date else "",
        'repair_description': str(wo.repair_description or ""),
        'spec_requirements': str(wo.spec_requirements or ""),
        'safety_instructions': str(wo.safety_instructions or ""),
        'job_instructions': str(wo.job_instructions or ""),
        'fc_system': str(wo.fc_system or ""),
        'fc_component': str(wo.fc_component or ""),
        'fc_failure_mode': str(wo.fc_failure_mode or ""),
        'fc_action': str(wo.fc_action or ""),
        'repair_service_report': str(wo.repair_service_report or ""),
    }
    
    template_path = settings.BASE_DIR / 'work_orders' / 'templates' / 'work_orders' / 'work_order_template.pdf'
    try:
        template = pdfrw.PdfReader(template_path)
    except Exception as e:
        return HttpResponse(f"Error finding PDF at {template_path}: {e}")
    
    for page in template.pages:
        annotations = page.get('/Annots')
        if annotations:
            for annotation in annotations:
                if annotation.get('/Subtype') == '/Widget':
                    key = annotation.get('/T')
                    if key:
                        key = key.to_unicode()
                        if key in data_dict:
                            annotation.update(
                                pdfrw.PdfDict(V='{}'.format(data_dict[key]))
                            )
    template.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))
    
    barcode_buffer = io.BytesIO()
    can = canvas.Canvas(barcode_buffer, pagesize=letter)
    
    if wo.barcode_image:
        barcode_path = wo.barcode_image.path
        can.drawImage(barcode_path, 360, 692, width=150, height=40, mask='auto')

        can.showPage()
        can.save()
        barcode_buffer.seek(0)
        barcode_pdf = pdfrw.PdfReader(barcode_buffer)
        template_page = template.pages[0]
        barcode_page = barcode_pdf.pages[0]
        merger = pdfrw.PageMerge(template_page)
        merger.add(barcode_page).render()
        
    output_buffer = io.BytesIO()
    pdfrw.PdfWriter().write(output_buffer, template)
    output_buffer.seek(0)
                            
    return FileResponse(output_buffer, as_attachment=True, filename=f"WorkOrder_{wo.work_order}.pdf", content_type='application/pdf')

def load_components(request):
    equipment_id = request.GET.get('equipment') 
    if equipment_id:
        components = Component.objects.filter(Equipment__id=equipment_id)
    else:
        components = Component.objects.none()
    return render(request, 'work_orders/component_warranty_table.html', {'components': components})