from django.shortcuts import render, redirect, get_object_or_404
from .models import Purchase, PurchaseLine
from .forms import PurchaseForm, PurchaseLineFormSet
from inventory.models import InventoryItem
from django.contrib import messages
from django.http import JsonResponse, FileResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib import colors
import os, openpyxl

try:
    from work_orders.models import WorkOrder
except Exception:
    WorkOrder = None
try:
    from facilities.models import CostCentre
except Exception:
    CostCentre = None
    
def purchasing(request):
    return render(request, 'purchasing/purchasing.html')

def purchases(request):
    return render(request, 'purchasing/purchases.html')

def create_purchase(request):
    next_url = request.GET.get('next')
    work_order_id = request.GET.get('work_order')
    
    if request.method == 'POST':
        print("POST Data Keys:", request.POST.keys())
        form = PurchaseForm(request.POST)
        formset = PurchaseLineFormSet(request.POST, prefix='lines')
        
        if form.is_valid() and formset.is_valid():
            purchase = form.save()
            formset.instance = purchase
            lines = formset.save(commit=False)
              
            for line in lines:
                if line.part_number_input:
                    line.purchase = purchase
                if line.inventory_item:
                    inv = line.inventory_item
                    line.part_number_input = inv.part_number
                    line.manufacturer = inv.manufacturer
                    line.part_description = line.part_description or inv.part_description
                    line.uom = line.uom or inv.uom
                    line.supplier = line.supplier or inv.supplier
                    if not line.unit_price:
                        line.unit_price = inv.unit_price
               
                line.save()
                
            for obj in formset.deleted_objects:
                obj.delete()
                
            purchase.update_grand_total()
            
            destination = request.POST.get('action_destination')
            next_url = request.GET.get('next')
            messages.success(request, f'Purchase {purchase.purchase_number} saved successfully.')
            if destination == 'return' and next_url:
                return redirect(next_url)
            return redirect('purchasing:purchases')
        else:
            print("Form Errors:", form.errors)
            print("Formset Errors:", formset.errors)
    else:
        initial_data = {}
        
        if work_order_id:
            initial_data['bill_location'] = 'Work Order'
            initial_data['wo_cc'] = work_order_id
            
        form = PurchaseForm(initial=initial_data)
        formset = PurchaseLineFormSet(prefix='lines')
        
    return render(request, 'purchasing/create_purchase.html', {
        'form': form,
        'formset': formset,
        'next': next_url,
    })
    
def purchase_detail(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    return render(request, 'purchasing/purchase_detail.html', {'purchase': purchase})

def purchase_number_preview(request):
    purchase_type = request.GET.get('purchase_type')
    if purchase_type not in ['P', 'R', 'S']:
        return JsonResponse({'preview': ''})
    year = timezone.now().strftime('%y')
    last_item = (
        Purchase.objects
        .filter(purchase_number__startswith=f"{purchase_type}{year}")
        .order_by('purchase_number')
        .last()
    )
    if last_item:
        last_no = int(last_item.purchase_number[3:])
        next_no = str(last_no + 1).zfill(6)
    else:
        next_no = '000001'
    return JsonResponse({'preview': f'{purchase_type}{year}{next_no}'})

def get_wo_cc_options(request):
    bill_location = request.GET.get('bill_location')
    options = []
    if bill_location == 'Work Order':
        if WorkOrder:
            options = [
                {
                    'value': str(obj),
                    'label': str(obj),
                }
                for obj in WorkOrder.objects.all()[:500]
            ]
        else:
            options = [
                {'value': 'WO1001', 'label': 'WO1001'},
                {'value': 'WO1002', 'label': 'WO1002'},
            ]
    elif bill_location == 'Cost Centre':
        if CostCentre:
            options = [
                {
                    'value': str(obj),
                    'label': str(obj),
                }
                for obj in CostCentre.objects.all()[:500]
            ]
        else:
            options = [
                {'value': 'CC100', 'label': 'CC100'},
                {'value': 'CC200', 'label': 'CC200'},
            ]
    return JsonResponse({'options': options})

def get_part_details(request):
    part_number = request.GET.get('part_number', '').strip()
    if not part_number:
        return JsonResponse({'found': False})
    try:
        item = InventoryItem.objects.select_related('supplier').get(part_number=part_number)
        return JsonResponse({
            'found': True,
            'inventory_id': item.id,
            'part_number': getattr(item, 'part_number', ''),
            'part_description': getattr(item, 'part_description', ''),
            'uom': getattr(item, 'uom', ''),
            'supplier_id': item.supplier.id if getattr(item, 'supplier', None) else '',
            'unit_price': str(getattr(item, 'unit_price', '0.00')),
        })
    except InventoryItem.DoesNotExist:
        return JsonResponse({'found': False})
    
def get_part_options(request):
    part_no = request.GET.get('part_number', '').strip()
    
    if not part_no:
        return JsonResponse({'options': []})
    
    main_items = InventoryItem.objects.filter(part_number__iexact=part_no).select_related('supplier')
    
    results = []
    seen_ids = set()
    
    for item in main_items:
        if item.id not in seen_ids:
            results.append(serialize_item(item, is_alternative=False))
            seen_ids.add(item.id)
        
        for alt in item.alternatives.all():
            if alt.id not in seen_ids:
                results.append(serialize_item(alt, is_alternative=True, original_part=item.part_number))
                seen_ids.add(alt.id)
            
    return JsonResponse({'options': results})

def serialize_item(item, is_alternative=False, original_part=None):
    supplier_display = str(item.supplier) if item.supplier else "No Supplier"
    
    return {
        'id': item.id,
        'part_number': item.part_number,
        'manufacturer': item.manufacturer or "N/A",
        'supplier_name': supplier_display,
        'supplier_id': item.supplier.id if item.supplier else '',
        'unit_price': str(item.unit_price),
        'description': item.part_description,
        'uom': item.uom,
        'is_alt': is_alternative,
        'linked_to': original_part
    }
    
def edit_purchase(request, pk=None):
    purchase = None
    if pk is not None:
        purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        if not purchase:
            messages.error(request, 'No purchase selected.')
            return redirect('purchasing:edit_purchase')
        form = PurchaseForm(request.POST, instance=purchase)
        formset = PurchaseLineFormSet(request.POST, instance=purchase, prefix='lines')
        if form.is_valid() and formset.is_valid():
            purchase = form.save()
            lines = formset.save(commit=False)
            
            for line in lines:
                if line.part_number_input:
                    line.purchase = purchase
                if line.inventory_item:
                    inv = line.inventory_item
                    line.part_number_input = inv.part_number
                    line.manufacturer = inv.manufacturer
                    line.part_description = line.part_description or inv.part_description
                    line.uom = line.uom or inv.uom
                    line.supplier = line.supplier or inv.supplier
                    if not line.unit_price:
                        line.unit_price = inv.unit_price
               
                line.save()
                
            for obj in formset.deleted_objects:
                obj.delete()
                
            purchase.update_grand_total()
            messages.success(request, f'Purchase {purchase.purchase_number} updated successfully.')
            return redirect('purchasing:purchases')
        else:
            print("Form Errors:", form.errors)
            print("Formset Errors:", formset.errors)
    else:
        if purchase:
            form = PurchaseForm(instance=purchase)
            formset = PurchaseLineFormSet(instance=purchase, prefix='lines')
        else:
            form = PurchaseForm()
            formset = PurchaseLineFormSet(prefix='lines')
    return render(request, 'purchasing/edit_purchase.html', {
        'form': form,
        'formset': formset,
        'purchase': purchase,
    })
    
def purchase_search_options(request):
    term = request.GET.get('term', '').strip()
    qs = Purchase.objects.all().order_by('-id')
    if term:
        qs = qs.filter(purchase_number__icontains=term)
    results = [
        {
            'id': p.id,
            'label': f'{p.purchase_number} - {p.wo_cc}',
        }
        for p in qs[:50]
    ]
    return JsonResponse({'results': results})
    
def search_purchase_load(request):
    purchase_id = request.GET.get('purchase_id')
    if not purchase_id:
        messages.error(request, 'Please select a purchase.')
        return redirect('purchasing:edit_purchase')
    purchase = Purchase.objects.filter(pk=purchase_id).first()
    if not purchase:
        messages.error(request, 'Purchase not found.')
        return redirect('purchasing:edit_purchase')
    return redirect('purchasing:edit_purchase_loaded', pk=purchase.pk)

def print_purchase_pdf(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf.setTitle(f"{purchase.purchase_number}")
    
    def draw_template_elements(p):
        # 1. Logo (Top Left)
        logo_path = "static/Images/TARMOR.png"
        if os.path.exists(logo_path):
            # Adjust width/height (120x40) to fit your specific PNG aspect ratio
            p.drawImage(logo_path, 40, height - 65, width=160, height=40, mask='auto')

        # 3. Barcode (Below Title)
        barcode_x = width - 200
        barcode_y = height - 65
        if purchase.barcode_image and os.path.exists(purchase.barcode_image.path):
            p.drawImage(purchase.barcode_image.path, barcode_x, barcode_y, width=160, height=45)
           
    # 2. Ship To Section (Left)
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(40, height - 80, "Ship to:")
        p.setFont("Helvetica", 10)
        ship_to_y = height - 95
        purchase.company_name = "TARMOR Inc."
        address_lines = [purchase.company_name, "c/o Facility", "Street Address", "City, Prov", "Postal Code"]
        for line in address_lines:
            p.drawString(40, ship_to_y, str(line))
            ship_to_y -= 12
            
    # 3. Order Info Boxes (Right)
        box_x = 400
        p.setFont("Helvetica-Bold", 10)
        labels = [("Purchase Order", purchase.purchase_number), ("Date", str(purchase.date))]
        label_y = height - 80
        for label, value in labels:
            p.drawRightString(box_x - 10, label_y + 5, f"{label}")
            p.rect(box_x, label_y, 150, 18) # Draw the data boxes
            p.drawString(box_x + 5, label_y + 5, str(value))
            label_y -= 25
            
    # 4. Table Header
        table_y = height - 210
        p.setFont("Helvetica-Bold", 10)
        # Column outlines
        p.rect(40, 100, 515, height - 310) # Main table border
        header_y = table_y + 5
        p.drawString(45, header_y, "Qty")
        p.drawString(85, header_y, "Part Number")
        p.drawString(185, header_y, "Part Desc")
        p.drawString(405, header_y, "Cost / Unit")
        p.drawString(485, header_y, "Total Cost")
        
        # Table Grid Lines (Verticals)
        p.line(80, 100, 80, table_y + 20)
        p.line(180, 100, 180, table_y + 20)
        p.line(400, 100, 400, table_y + 20)
        p.line(480, 100, 480, table_y + 20)
        p.line(40, table_y, 555, table_y) # Horizontal header line
        
        return table_y - 15
    
    y = draw_template_elements(pdf)
    pdf.setFont("Helvetica", 9)
    
    for line in purchase.lines.all():
        if y < 120: # Page break logic
            pdf.showPage()
            y = draw_template_elements(pdf)
            pdf.setFont("Helvetica", 9)
        
        pdf.drawString(45, y, str(line.qty))
        pdf.drawString(85, y, str(line.part_number_input)[:15])
        pdf.drawString(185, y, str(line.part_description)[:45])
        pdf.drawRightString(475, y, f"{line.unit_price}")
        pdf.drawRightString(550, y, f"{line.total_price}")
        y -= 20 # Row height matching the grid
        
    # Grand Total Box
    pdf.rect(480, 80, 75, 20)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawRightString(475, 85, "Total")
    pdf.drawString(485, 85, f"$ {purchase.grand_total}")
    
    # Footer
    pdf.setFont("Helvetica", 8)
    pdf.drawString(40, 40, "Page 1 of 1")
    pdf.drawRightString(555, 40, "2026/02/12")
    
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    filename = f"{purchase.purchase_number}.pdf"
    return FileResponse(buffer, as_attachment=False, filename=filename)

def search_purchases(request):
    purchase_number = request.GET.get('purchase_number', '').strip()
    wo_cc = request.GET.get('wo_cc', '').strip()
    part_number_input = request.GET.get('part_number_input', '').strip()
    supplier = request.GET.get('supplier', '').strip()
    row_status = request.GET.get('row_status', '').strip()
    
    sort_by = request.GET.get('sort', '-purchase_number')

    purchase_lines = PurchaseLine.objects.select_related(
        'purchase',
        'supplier',
        'inventory_item',
    ).all()
    
    wo_list = list(
        WorkOrder.objects.values_list('work_order', flat=True)
        .distinct()
        .order_by('work_order')
    )
    cc_list = list(
        CostCentre.objects.values_list('Cost_Centre', flat=True)
        .distinct()
        .order_by('Cost_Centre')
    )
    wo_cc_options = sorted(wo_list + cc_list)

    if purchase_number:
        purchase_lines = purchase_lines.filter(
            purchase__purchase_number__icontains=purchase_number
        )
    if wo_cc:
        purchase_lines = purchase_lines.filter(
            purchase__wo_cc__icontains=wo_cc
        )
    if part_number_input:
        purchase_lines = purchase_lines.filter(
            Q(part_number_input__icontains=part_number_input) 
        )
    if supplier:
        purchase_lines = purchase_lines.filter(
            supplier__supplier_name__icontains=supplier
        )
    if row_status:
        purchase_lines = purchase_lines.filter(
            row_status=row_status
        )

    sort_mapping = {
        'purchase_number': 'purchase__purchase_number',
        '-purchase_number': '-purchase__purchase_number',
        'wo_cc': 'purchase__wo_cc',
        '-wo_cc': '-purchase__wo_cc',
        'supplier': 'supplier__supplier_name',
        '-supplier': '-supplier__supplier_name',
        'status': 'row_status',
        '-status': '-row_status',
        'id': 'id',
        '-id': '-id',
    }
    
    final_sort = sort_mapping.get(sort_by, '-purchase__id')
    purchase_lines = purchase_lines.order_by(final_sort)

    purchase_number_options = (
        Purchase.objects.values_list('purchase_number', flat=True)
        .distinct().order_by('purchase_number')
    )
    
    wo_cc_options = (
        Purchase.objects.exclude(Q(wo_cc__isnull=True) | Q(wo_cc=''))
        .values_list('wo_cc', flat=True)
        .distinct().order_by('wo_cc')
    )
    
    part_number_input_options = (
        PurchaseLine.objects.exclude(Q(part_number_input__isnull=True) | Q(part_number_input=''))
        .values_list('part_number_input', flat=True)
        .distinct().order_by('part_number_input')
    )
            
    supplier_options = (
        PurchaseLine.objects.select_related('supplier')
        .exclude(supplier__isnull=True)
        .values_list('supplier__supplier_name', flat=True)
        .distinct()
        .order_by('supplier__supplier_name')
    )
    row_status_choices = PurchaseLine._meta.get_field('row_status').choices

    context = {
        'purchase_lines': purchase_lines,
        'purchase_number': purchase_number,
        'wo_cc': wo_cc,
        'part_number_input': part_number_input,
        'supplier': supplier,
        'row_status': row_status,
        'sort': sort_by,
        'purchase_number_options': purchase_number_options,
        'wo_cc_options': wo_cc_options,
        'part_number_input_options': part_number_input_options,
        'supplier_options': supplier_options,
        'row_status_choices': row_status_choices,
    }
    return render(request, 'purchasing/search_purchases.html', context)

def export_purchases_excel(request):
    purchase_number = request.GET.get('purchase_number', '').strip()
    wo_cc = request.GET.get('wo_cc', '').strip()
    part_number_input = request.GET.get('part_number_input', '').strip()
    supplier = request.GET.get('supplier', '').strip()
    row_status = request.GET.get('row_status', '').strip()

    purchase_lines = PurchaseLine.objects.select_related(
        'purchase', 'supplier', 'inventory_item'
    ).all()

    if purchase_number:
        purchase_lines = purchase_lines.filter(purchase__purchase_number__icontains=purchase_number)
    if wo_cc:
        purchase_lines = purchase_lines.filter(purchase__wo_cc__icontains=wo_cc)
    if part_number_input:
        purchase_lines = purchase_lines.filter(part_number_input__icontains=part_number_input)
    if supplier:
        purchase_lines = purchase_lines.filter(supplier__supplier_name__icontains=supplier)
    if row_status:
        purchase_lines = purchase_lines.filter(row_status=row_status)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Purchases"

    headers = ['Purchase #', 'WO/CC', 'Part Number', 'Manufacturer', 'Description', 'Supplier', 'Qty', 'UoM', 'Unit Price', 'Total Price', 'Status']
    ws.append(headers)

    for line in purchase_lines:
        ws.append([
            line.purchase.purchase_number if line.purchase else '',
            line.purchase.wo_cc if line.purchase else '',
            line.part_number_input,
            line.manufacturer,
            line.part_description,
            line.supplier.supplier_name if line.supplier else '',
            line.qty if line.qty else '',
            line.uom if line.uom else '',
            line.unit_price if line.unit_price else '',
            line.total_price if line.total_price else '',
            line.get_row_status_display(),
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="purchases_export.xlsx"'
    wb.save(response)
    return response