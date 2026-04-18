from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Supplier
from .forms import NewSupplierForm
from django.http import HttpResponse
import openpyxl

def suppliers(request):
    return render(request, 'suppliers/suppliers.html')

def add_supplier(request):
    supplier = Supplier()
    
    if request.method == 'POST':
        new_sup_form = NewSupplierForm(request.POST, instance=supplier)
        
        if new_sup_form.is_valid():
            new_sup_form.save()
            messages.success(request, "Supplier added successfully!")
            return redirect("suppliers:suppliers")
        else:
            messages.error(request, "There was an error saving the supplier. Please check the fields below.")
            
    else:
        new_sup_form = NewSupplierForm()
            
    return render(request, 'suppliers/add_supplier.html', {
        'new_sup_form': new_sup_form,
    })
    
def edit_supplier(request):
    supplier = None
    supplier_name = request.GET.get('supplier_name', '')

    if supplier_name:
        supplier = Supplier.objects.filter(supplier_name__icontains=supplier_name,).first()

    if request.method == 'POST':
        sup_id = request.POST.get('supplier_id')
        supplier = get_object_or_404(Supplier, id=sup_id)
        form = NewSupplierForm(request.POST, instance=supplier)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier updated successfully!")
            return redirect('suppliers:suppliers')
        else:
            messages.error(request, "There was an error saving the supplier. Please check the fields below.")
    else:
        form = NewSupplierForm(instance=supplier)

    return render(request, 'suppliers/edit_supplier.html', {
        'new_sup_form': form,
        'supplier': supplier,
        'supplier_name': supplier_name
    })
    
def search_suppliers(request):
    supplier_name = request.GET.get('supplier_name', '')
    province_state = request.GET.get('province_state', '')
    status = request.GET.get('status', '')

    sort_by = request.GET.get('sort', 'supplier_name')
    suppliers = Supplier.objects.all()

    if supplier_name:
        suppliers = suppliers.filter(supplier_name__icontains=supplier_name)
    if province_state:
        suppliers = suppliers.filter(province_state__icontains=province_state)
    if status:
        suppliers = suppliers.filter(status__icontains=status)

    params = request.GET.copy()
    if 'sort' in params:
        del params['sort']
    filter_url = params.urlencode()

    context = {
        'suppliers': suppliers,
        'filter_url': filter_url,
        'sort_by': sort_by,
        'supplier_name': supplier_name,
        'province_state': province_state,
        'status': status
    }
    return render(request, 'suppliers/search_suppliers.html', context)

def export_suppliers_excel(request):
    supplier_name = request.GET.get('supplier_name', '')
    province_state = request.GET.get('province_state', '')
    status = request.GET.get('status', '')
    
    suppliers = Supplier.objects.all()

    if supplier_name:
        suppliers = suppliers.filter(supplier_name__icontains=supplier_name)
    if province_state:
        suppliers = suppliers.filter(province_state__icontains=province_state)
    if status:
        suppliers = suppliers.filter(status__icontains=status)
        
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Suppliers"

    columns = ['supplier_name', 'status', 'street_address', 'city', 'province_state', 'country', 
                'postal_zip','contact', 'phone', 'email', 'supplier_discount', 'payment_method',
                'supplier_currency']
    
    ws.append(columns)

    for suppliers in suppliers:
        ws.append([
            suppliers.supplier_name,
            suppliers.status,
            suppliers.street_address, 
            suppliers.city,
            suppliers.province_state, 
            suppliers.country,
            suppliers.postal_zip,
            suppliers.contact,
            suppliers.phone,
            suppliers.email,
            suppliers.supplier_discount,
            suppliers.payment_method,
            suppliers.supplier_currency
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Suppliers_Export.xlsx"'
    wb.save(response)
    return response