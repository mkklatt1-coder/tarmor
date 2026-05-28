from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CostCentreUploadForm, FacilityUploadForm
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .models import CostCentre, Facility
from openpyxl import Workbook
from django.http import HttpResponse
import openpyxl

def facilities(request):
    return render(request, "facilities/facilities.html")

def costcentre_upload(request):
    if request.method == "POST":
        costcentreuploadform = CostCentreUploadForm(request.POST)
        if costcentreuploadform.is_valid():
            costcentre = costcentreuploadform.save()
            messages.success(request, f"Cost Centre {costcentre.Cost_Centre} created successfully.")
            return redirect("facilities:facilities")
    else:
        costcentreuploadform = CostCentreUploadForm()
    
    try:
        preview_cc = CostCentre.generate_next_cost_centre()
    except Exception:
        preview_cc = "G00000001"

    return render(
        request,
        "facilities/add_costcentre.html",
        {
            "costcentreuploadform": costcentreuploadform,
            "preview_cc": preview_cc,
        },
    )

def search_costcentre(request):
    cost_centre = request.GET.get('Cost_Centre', '').strip()
    cost_centre_description = request.GET.get('Cost_Centre_Description', '').strip()
    status = request.GET.get('Status', '').strip()
    
    clean_cc = cost_centre.split(' - ')[0].strip() if ' - ' in cost_centre else cost_centre

    costcentre_list = CostCentre.objects.all()
    
    if clean_cc:
        costcentre_list = costcentre_list.filter(Cost_Centre__icontains=clean_cc)
    if cost_centre_description:
        costcentre_list = costcentre_list.filter(Cost_Centre_Description__icontains=cost_centre_description)
    if status:
        costcentre_list = costcentre_list.filter(Status=status)

    sort_by = request.GET.get('sort', 'Cost_Centre')
    is_descending = sort_by.startswith('-')
    clean_sort_key = sort_by.lstrip('-')

    sort_mapping = {
        'Cost_Centre': 'Cost_Centre',
        'Cost_Centre_Description': 'Cost_Centre_Description',
        'Status': 'Status',
    }
   
    if clean_sort_key in sort_mapping:
        db_field = sort_mapping[clean_sort_key]
        order_field = f"-{db_field}" if is_descending else db_field
        costcentre_list = costcentre_list.order_by(order_field)
    else:
        costcentre_list = costcentre_list.order_by('Cost_Centre')

    all_cc_records = CostCentre.objects.all().only('Cost_Centre', 'Cost_Centre_Description').order_by('Cost_Centre')
    all_descriptions = CostCentre.objects.exclude(Cost_Centre_Description__isnull=True).values_list('Cost_Centre_Description', flat=True).distinct().order_by('Cost_Centre_Description')
    all_statuses = CostCentre.objects.exclude(Status__isnull=True).values_list('Status', flat=True).distinct().order_by('Status')

    params = request.GET.copy()
    if 'sort' in params:
        del params['sort']
    filter_url = params.urlencode()

    return render(request, 'facilities/search_costcentre.html', {
        'costcentre_list': costcentre_list, 
        'sort': sort_by,
        'filter_url': filter_url,
        'all_cc_records': all_cc_records,
        'all_descriptions': all_descriptions,
        'all_statuses': all_statuses,
        'cost_centre_val': cost_centre,
        'cost_centre_description_val': cost_centre_description,
        'status_val': status,
    })

class CostCentreUpdateView(UpdateView):
    model = CostCentre
    form_class = CostCentreUploadForm
    template_name = "facilities/edit_costcentre.html"
    success_url = reverse_lazy("facilities:facilities")
    
def edit_costcentre(request, pk=None):
    all_cc_suggestions = CostCentre.objects.all().only('Cost_Centre', 'Cost_Centre_Description').order_by('Cost_Centre')
    search_id = request.GET.get('q', '').strip()
    clean_search = search_id.split(' - ')[0].strip() if ' - ' in search_id else search_id
    
    if clean_search:
        instance = CostCentre.objects.filter(Cost_Centre=clean_search).first()
        if instance:
            return redirect('facilities:edit_costcentre', pk=instance.pk)
        else:
            messages.error(request, f"Cost Centre '{clean_search}' not found.")
            return redirect('facilities:edit_costcentre')

    instance = get_object_or_404(CostCentre, pk=pk) if pk else None
    
    if request.method == "POST":
        form = CostCentreUploadForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Cost Centre updated successfully.")
            return redirect('facilities:facilities')
    else:
        form = CostCentreUploadForm(instance=instance)

    return render(request, 'facilities/edit_costcentre.html', {
        'form': form,
        'instance': instance,
        'all_cc_suggestions': all_cc_suggestions,
        'search_val': search_id or (instance.Cost_Centre if instance else "")
    })
    
def export_costcentre_excel(request):
    
    cost_centre = request.GET.get('Cost_Centre','').strip()
    cost_centre_description = request.GET.get('Cost_Centre_Description','').strip()
    status = request.GET.get('Status','').strip()

    queryset = CostCentre.objects.all()
    if cost_centre:
        costcentre_list = costcentre_list.filter(Cost_Centre__icontains=cost_centre)
    if cost_centre_description:
        costcentre_list = costcentre_list.filter(Cost_Centre_Description__name__icontains=cost_centre_description)
    if status:
        costcentre_list = costcentre_list.filter(Status=status)

    wb = Workbook()
    ws = wb.active
    ws.title = "Cost Centres"

    headers = ["Cost Centre", "Description", "Status"]
    ws.append(headers)

  
    for cc in queryset:
        ws.append([cc.Cost_Centre, cc.Cost_Centre_Description, cc.Status])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="cost_centres.xlsx"'
    wb.save(response)
    return response

def facility_upload(request):
    if request.method == "POST":
        facilityuploadform = FacilityUploadForm(request.POST)
        if facilityuploadform.is_valid():
            facility = facilityuploadform.save()
            messages.success(
                request,
                f"Facility {facility.Facility_Name} created successfully."
            )
            return redirect("facilities:facilities")
    else:
        facilityuploadform = FacilityUploadForm()
    return render(
        request,
        "facilities/add_facility.html",
        {
            "facilityuploadform": facilityuploadform,
        },
    )
    
def edit_facility(request, pk=None):
    search_name = request.GET.get("Facility_Name", "").strip()
    matches = None
    instance = None
    # Search flow
    if search_name and pk is None and request.method == "GET":
        matches = Facility.objects.filter(
            Facility_Name__icontains=search_name
        ).order_by("Facility_Name")
        match_count = matches.count()
        if match_count == 1:
            return redirect("facilities:edit_facility", pk=matches.first().pk)
        if match_count > 1:
            messages.warning(
                request,
                f"Multiple facilities matched '{search_name}'. Please select one."
            )
            form = FacilityUploadForm()
            return render(request, "facilities/edit_facility.html", {
                "form": form,
                "instance": None,
                "Facility_Name": search_name,
                "matches": matches,
            })
        messages.error(request, f"Facility '{search_name}' not found.")
        form = FacilityUploadForm()
        return render(request, "facilities/edit_facility.html", {
            "form": form,
            "instance": None,
            "Facility_Name": search_name,
            "matches": None,
        })
    # Load selected facility for editing
    if pk is not None:
        instance = get_object_or_404(Facility, pk=pk)
    # Save flow
    if request.method == "POST":
        form = FacilityUploadForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Facility updated successfully.")
            return redirect("facilities:facilities")
    else:
        form = FacilityUploadForm(instance=instance)
    return render(request, "facilities/edit_facility.html", {
        "form": form,
        "instance": instance,
        "Facility_Name": search_name or (instance.Facility_Name if instance else ""),
        "matches": matches,
    })
    
def search_facilities(request):
    facility_code = request.GET.get("Facility_Code", "").strip()
    facility_name = request.GET.get("Facility_Name", "").strip()
    cost_centre = request.GET.get("Cost_Centre", "").strip()
        
    facility_list = Facility.objects.all()
    if facility_code:
        facility_list = facility_list.filter(Facility_Code__icontains=facility_code)
    if facility_name:
        facility_list = facility_list.filter(Facility_Name__icontains=facility_name)
    if cost_centre:
        facility_list = facility_list.filter(Cost_Centre__Cost_Centre__icontains=cost_centre)

    sort_by = request.GET.get("sort", "Facility_Name")
    is_descending = sort_by.startswith('-')
    clean_sort_key = sort_by.lstrip('-')
    
    allowed_sort_fields = {
        "Facility_Code": "Facility_Code",
        "Facility_Name": "Facility_Name",
        "Cost_Centre": "Cost_Centre__Cost_Centre",
        "Street_Address": "Street_Address",
        "City": "City",
        "Province_State": "Province_State",
        "Country": "Country",
        "Postal_Zip_Code": "Postal_Zip_Code",
        "Contact_Name": "Contact_Name",
        "Contact_Phone_Number": "Contact_Phone_Number",
        "Email_Address": "Email_Address",
    }

    if clean_sort_key in allowed_sort_fields:
        db_field = allowed_sort_fields[clean_sort_key]
        order_field = f"-{db_field}" if is_descending else db_field
        facility_list = facility_list.order_by(order_field)
    else:
        facility_list = facility_list.order_by("Facility_Name")

    params = request.GET.copy()
    if 'sort' in params:
        del params['sort']
    filter_url = params.urlencode()

    return render(request, "facilities/search_facilities.html", {
        "facility_list": facility_list,
        "sort": sort_by,
        "filter_url": filter_url,
        "Facility_Code": facility_code,
        "Facility_Name": facility_name,
        "Cost_Centre": cost_centre,
    })

def export_facilities_excel(request):
    facility_code = request.GET.get("Facility_Code", "").strip()
    facility_name = request.GET.get("Facility_Name", "").strip()
    cost_centre = request.GET.get("Cost_Centre", "").strip()
    
    facility_list = Facility.objects.select_related('Cost_Centre').all()
    if facility_code:
        facility_list = facility_list.filter(Facility_Code__icontains=facility_code)
    if facility_name:
        facility_list = facility_list.filter(Facility_Name__icontains=facility_name)
    if cost_centre:
        facility_list = facility_list.filter(Cost_Centre__Cost_Centre__icontains=cost_centre)
        
    facility_list = facility_list.order_by("Facility_Name")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Facilities"

    headers = [
        "Facility Code", "Facility Name", "Cost Centre", "Street Address", 
        "City", "Province/State", "Country", "Postal/Zip Code", 
        "Contact Name", "Contact Phone Number", "Email Address"
    ]
    ws.append(headers)

    for fac in facility_list:
        cc_text = fac.Cost_Centre.Cost_Centre if fac.Cost_Centre else "---"
        ws.append([
            fac.Facility_Code,
            fac.Facility_Name,
            cc_text,
            fac.Street_Address or "---",
            fac.City or "---",
            fac.Province_State or "---",
            fac.Country or "---",
            fac.Postal_Zip_Code or "---",
            fac.Contact_Name or "---",
            fac.Contact_Phone_Number or "---",
            fac.Email_Address or "---"
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="Facilities_Export.xlsx"'
    wb.save(response)
    return response
