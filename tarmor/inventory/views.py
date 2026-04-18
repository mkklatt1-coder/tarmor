from django.shortcuts import render, redirect, get_object_or_404
from .models import InventoryItem
from django.contrib import messages
from django.utils import timezone
from .forms import InventoryItemForm, AlternativeFormSet
from django.http import HttpResponse
import openpyxl

def inventory(request):
    return render(request, 'inventory/inventory.html')

def add_inventory_item(request, pk=None):
    instance = get_object_or_404(InventoryItem, pk=pk) if pk else None
    
    if request.method == "POST":
        form = InventoryItemForm(request.POST, instance=instance)
        existing_alts = instance.alternatives.all() if instance else InventoryItem.objects.none()
        formset = AlternativeFormSet(request.POST, queryset=existing_alts, prefix='alt')

        if form.is_valid() and formset.is_valid():
            main_item = form.save()
            new_alternatives = formset.save()
            for alt in new_alternatives:
                main_item.alternatives.add(alt)
            messages.success(request, "Inventory item added successfully!")
            return redirect('inventory:inventory')
        else:
            messages.error(request, "There was an error saving the inventory item(s). Please check the fields below.")
            
    else:
        form = InventoryItemForm(instance=instance)
        existing_alts = instance.alternatives.all() if instance else InventoryItem.objects.none()
        formset = AlternativeFormSet(queryset=existing_alts, prefix='alt')

    return render(request, 'inventory/add_inventory_item.html', {
        'new_inv_form': form,
        'inv_formset': formset,
        'is_edit': bool(pk)
    })
    
def edit_inventory_item(request):
    part_num = request.GET.get('part_number')
    instance = None
    
    if part_num:
        instance = InventoryItem.objects.filter(part_number=part_num).first()
    
    if part_num and not instance:
        messages.error(request, f"Part number '{part_num}' not found.")
        return render(request, 'inventory/edit_inventory_item.html', {
            'new_inv_form': InventoryItemForm(),
            'inv_formset': AlternativeFormSet(queryset=InventoryItem.objects.none(), prefix='alt'),
            'instance': None
        })

    if request.method == "POST":
        part_num_from_post = request.POST.get('part_number') 
        instance = InventoryItem.objects.filter(part_number=part_num_from_post).first()
        form = InventoryItemForm(request.POST, instance=instance)
        existing_alts = instance.alternatives.all() if instance else InventoryItem.objects.none()
        formset = AlternativeFormSet(request.POST, queryset=existing_alts, prefix='alt')

        if form.is_valid() and formset.is_valid():
            main_item = form.save()
            new_alts = formset.save()
            for alt in new_alts:
                main_item.alternatives.add(alt)
            messages.success(request, "Inventory item updated successfully!")    
            return redirect('inventory:inventory')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = InventoryItemForm(instance=instance)
        existing_alts = instance.alternatives.all() if instance else InventoryItem.objects.none()
        formset = AlternativeFormSet(queryset=existing_alts, prefix='alt')

    return render(request, 'inventory/edit_inventory_item.html', {
        'new_inv_form': form,
        'inv_formset': formset,
        'instance': instance,
        'part_number': part_num,
    })

def delete_inventory_group(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Part and all associated data deleted.")
        return redirect('inventory:inventory')
    return redirect('inventory:edit_inventory_item')

def search_inventory(request):
    part_number = request.GET.get('part_number', '')
    supplier = request.GET.get('supplier', '')
    manufacturer = request.GET.get('manufacturer', '')
    controlled_product = request.GET.get('controlled_product', '')
   
    sort_by = request.GET.get('sort', 'part_number')
    inventory = InventoryItem.objects.all().distinct()

    if part_number:
        inventory = inventory.filter(part_number__icontains=part_number)
    if supplier:
        inventory = inventory.filter(supplier__supplier_name__icontains=supplier)
    if manufacturer:
        inventory = inventory.filter(manufacturer__icontains=manufacturer)
    if controlled_product:
        inventory = inventory.filter(controlled_product__icontains=controlled_product)

    inventory = inventory.order_by(sort_by)
    
    params = request.GET.copy()
    if 'sort' in params:
        del params['sort']
    filter_url = params.urlencode()

    context = {
        'inventory': inventory,
        'filter_url': filter_url,
        'sort_by': sort_by,
        'part_number': part_number,
        'supplier': supplier,
        'manufacturer': manufacturer,
        'controlled_product': controlled_product
    }
    return render(request, 'inventory/search_inventory.html', context)

def export_inventory_excel(request):
    part_number = request.GET.get('part_number', '')
    supplier = request.GET.get('supplier', '')
    manufacturer = request.GET.get('manufacturer', '')
    controlled_product = request.GET.get('controlled_product', '')
   
    inventory = InventoryItem.objects.all()

    if part_number:
        inventory = inventory.filter(part_number__icontains=part_number)
    if supplier:
        inventory = inventory.filter(supplier__supplier_name__icontains=supplier)
    if manufacturer:
        inventory = inventory.filter(manufacturer__icontains=manufacturer)
    if controlled_product:
        inventory = inventory.filter(controlled_product__icontains=controlled_product)
        
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventory"

    columns = ['part_number', 'part_description', 'supplier', 'manufacturer', 'qty', 'uom', 
                'unit_price','stock', 'controlled_product']

    ws.append(columns)

    for inv in inventory:
        supplier_display = inv.supplier.supplier_name if inv.supplier else ""
        ws.append([
            inv.part_number,
            inv.part_description,
            supplier_display,
            inv.manufacturer,
            inv.qty,
            inv.uom,
            inv.unit_price,
            inv.stock,
            inv.controlled_product,
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Inventory_Export.xlsx"'
    wb.save(response)
    return response

def export_manage_inventory_excel(request):
    manage_inventory = InventoryItem.objects.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Manage_Inventory"

    columns = [
        "Part Number", 
        "Part Description", 
        "Bin Location", 
        "Qty On Hand", 
        "Min Qty", 
        "Max Qty", 
        "UoM", 
        "Last Transaction Date", 
        "Last Transaction Number"]
        
    ws.append(columns)

    for manage in manage_inventory:
        last_date = manage.last_transaction_date.strftime('%Y-%m-%d %H:%M') if manage.last_transaction_date else ""
    
        ws.append([
            str(manage.part_number),
            str(manage.part_description),
            str(manage.bin_location or ""),
            manage.qty_onhand,
            manage.min_qty,
            manage.max_qty,
            str(manage.uom or ""),
            last_date,
            str(manage.last_transaction_number or ""),
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Manage_Inventory_Export.xlsx"'
    wb.save(response)
    return response

def manage_inventory(request):
    
    if request.method == "POST":
        item_id = request.POST.get('item_id')
        try:
            if item_id:
                item = get_object_or_404(InventoryItem, id=item_id)
            
                item.bin_location = request.POST.get('bin_location')
                item.qty_onhand = int(request.POST.get('qty_onhand') or 0)
                item.min_qty = int(request.POST.get('min_qty') or 0)
                item.max_qty = int(request.POST.get('max_qty') or 0)
                item.uom = request.POST.get('uom')
                
                now = timezone.now()
                item.last_transaction_date = now
                item.last_transaction_number = f"M{now.strftime('%Y%m%d')}"
                
                print(f"DEBUG: Saving Item {item_id} - New Bin: {item.bin_location}")
                item.save()
                messages.success(request, "Inventory item updated successfully!")
                return redirect('inventory:manage_inventory')
            else:
                messages.error(request, "Error: No item ID provided for update.")
        except Exception as e:
            messages.error(request, f"Error updating inventory item: {str(e)}")
            return redirect('inventory:manage_inventory')

    edit_id = request.GET.get('edit')
    edit_item = None
    if edit_id:
        edit_item = get_object_or_404(InventoryItem, id=edit_id)

    inventory_list = InventoryItem.objects.all().order_by('part_number')

    return render(request, 'inventory/manage_inventory.html', {
        'manage_inventory': inventory_list,
        'edit_item': edit_item,
    })