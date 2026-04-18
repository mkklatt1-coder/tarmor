from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CostCentreUploadForm, FacilityUploadForm
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .models import CostCentre, Facility
from openpyxl import Workbook
from django.http import HttpResponse

def facilities(request):
    return render(request, "facilities/facilities.html")

def costcentre_upload(request):
    if request.method == "POST":
        costcentreuploadform = CostCentreUploadForm(request.POST)
        if costcentreuploadform.is_valid():
            costcentre = costcentreuploadform.save()
            messages.success(
                request,
                f"Cost Centre {costcentre.Cost_Centre} created successfully."
            )
            return redirect("facilities:facilities")
    else:
        costcentreuploadform = CostCentreUploadForm()
    return render(
        request,
        "facilities/add_costcentre.html",
        {
            "costcentreuploadform": costcentreuploadform,
        },
    )

def search_costcentre(request):
    sort_by = request.GET.get('sort', 'Cost_Centre')
    
    cost_centre = request.GET.get('Cost_Centre','').strip()
    cost_centre_description = request.GET.get('Cost_Centre_Description','').strip()
    status = request.GET.get('Status','').strip()
    
    costcentre_list = CostCentre.objects.all()
    
    if cost_centre:
        costcentre_list = costcentre_list.filter(Cost_Centre__icontains=cost_centre)
    if cost_centre_description:
        costcentre_list = costcentre_list.filter(Cost_Centre_Description__name__icontains=cost_centre_description)
    if status:
        costcentre_list = costcentre_list.filter(Status=status)
   
    costcentre_list = costcentre_list.order_by(sort_by)
    return render(request, 'facilities/search_costcentre.html', {'costcentre_list': costcentre_list, 'sort_by': sort_by})

class CostCentreUpdateView(UpdateView):
    model = CostCentre
    form_class = CostCentreUploadForm
    template_name = "facilities/edit_costcentre.html"
    success_url = reverse_lazy("facilities:facilities")
    
def edit_costcentre(request, pk=None):
    search_id = request.GET.get('q')
    if search_id:
        instance = CostCentre.objects.filter(Cost_Centre=search_id).first()
        if instance:
            return redirect('facilities:edit_costcentre', pk=instance.pk)
        else:
            messages.error(request, f"Cost Centre '{search_id}' not found.")
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
        'Cost_Centre': search_id or (instance.Cost_Centre if instance else "")
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
    
    sort_by = request.GET.get("sort", "Facility_Name")
    
    allowed_sort_fields = {
        "Facility_Code": "Facility_Code",
        "Facility_Name": "Facility_Name",
        "Cost_Centre": "Cost_Centre",
        "Street_Address_1": "Street_Address_1",
        "City": "City",
        "Province_State": "Province_State",
        "Country": "Country",
        "Postal_Zip_Code": "Postal_Zip_Code",
        "Contact_Name": "Contact_Name",
        "Contact_Phone_Number": "Contact_Phone_Number",
        "Email_Address": "Email_Address",
        "Additional_Information": "Additional_Information",
    }
    
    facility_list = Facility.objects.all()
    if facility_code:
        facility_list = facility_list.filter(Facility_Code__icontains=facility_code)
    if facility_name:
        facility_list = facility_list.filter(Facility_Name__icontains=facility_name)
    if cost_centre:
        facility_list = facility_list.filter(Cost_Centre__Cost_Centre__icontains=cost_centre)
        
    facility_list = facility_list.order_by(allowed_sort_fields.get(sort_by, "Facility_Name"))
    return render(request, "facilities/search_facilities.html", {
        "facility_list": facility_list,
        "sort_by": sort_by,
        "Facility_Code": facility_code,
        "Facility_Name": facility_name,
        "Cost_Centre": cost_centre,
    })


