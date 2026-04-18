from django.contrib import messages
from django import forms
from django.http import HttpResponse
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory, modelform_factory
from django.db.models import Count, Max, Min
from .models import Employee, EmployeeCertification, Crew, CrewShiftRotation, ShiftPattern
from .forms import (
    NewEmployeeForm,
    CertificationFormSet,
    EmployeeCertificationForm,
    CrewShiftRotationUploadForm,
    ShiftPatternForm,
    ReplaceScheduleBatchForm,
)
import openpyxl, datetime, calendar, holidays, uuid
from datetime import date, timedelta
from facilities.models import Facility

# --- DASHBOARD ---
def personnel(request):
    return render(request, 'personnel/personnel.html')

# --- EMPLOYEE MANAGEMENT ---
def add_employee(request):
    employee = Employee()
    if request.method == 'POST':
        new_emp_form = NewEmployeeForm(request.POST, instance=employee)
        cert_formset = CertificationFormSet(
            request.POST,
            instance=employee,
            prefix='cert'
        )
        if new_emp_form.is_valid() and cert_formset.is_valid():
            with transaction.atomic():
                employee = new_emp_form.save()
                cert_formset.instance = employee
                cert_formset.save()
            messages.success(request, 'Employee added successfully.')
            return redirect('personnel:personnel')
    else:
        new_emp_form = NewEmployeeForm(instance=employee)
        cert_formset = CertificationFormSet(instance=employee, prefix='cert')
    return render(request, 'personnel/add_employee.html', {
        'new_emp_form': new_emp_form,
        'cert_formset': cert_formset,
    })
    
def edit_employee(request):
    employee = None
    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')

    if first_name and last_name:
        employee = Employee.objects.filter(
            First_Name__icontains=first_name,
            Last_Name__icontains=last_name
        ).first()

    CertificationFormSet = inlineformset_factory(
        Employee, EmployeeCertification,
        form=EmployeeCertificationForm,
        fields=('Certification', 'Institution', 'Date_Cert', 'Renewable', 'Renewal_Cost'),
        extra=0, can_delete=True
    )

    if request.method == 'POST':
        emp_id = request.POST.get('employee_id')
        employee = get_object_or_404(Employee, id=emp_id)
        form = NewEmployeeForm(request.POST, instance=employee)
        formset = CertificationFormSet(request.POST, instance=employee, prefix='cert')
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('personnel:personnel')
    else:
        form = NewEmployeeForm(instance=employee)
        formset = CertificationFormSet(instance=employee, prefix='cert')

    return render(request, 'personnel/edit_employee.html', {
        'new_emp_form': form,
        'cert_formset': formset,
        'employee': employee,
        'first_name': first_name,
        'last_name': last_name
    })
    
# --- SEARCH & FILTERING ---
def search_employee(request):
    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    position = request.GET.get('position', '')
    location = request.GET.get('location', '')
    status = request.GET.get('status', '')

    sort_by = request.GET.get('sort', 'Last_Name')
    employees = Employee.objects.all()

    if first_name:
        employees = employees.filter(First_Name__icontains=first_name)
    if last_name:
        employees = employees.filter(Last_Name__icontains=last_name)
    if position:
        employees = employees.filter(Position__icontains=position)
    if location:
        employees = employees.filter(Location__icontains=location)
    if status:
        employees = employees.filter(Status__icontains=status)

    params = request.GET.copy()
    if 'sort' in params:
        del params['sort']
    filter_url = params.urlencode()

    context = {
        'employees': employees,
        'filter_url': filter_url,
        'sort_by': sort_by,
        'first_name': first_name,
        'last_name': last_name,
        'position': position,
        'location': location,
        'status': status
    }
    return render(request, 'personnel/search_employee.html', context)

def search_certifications(request):
    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    position = request.GET.get('position', '')
    location = request.GET.get('location', '')
    status = request.GET.get('status', '')

    sort_by = request.GET.get('sort', 'Employee__Last_Name')
    certs = EmployeeCertification.objects.all()

    if first_name:
        certs = certs.filter(Employee__First_Name__icontains=first_name)
    if last_name:
        certs = certs.filter(Employee__Last_Name__icontains=last_name)
    if position:
        certs = certs.filter(Employee__Position__icontains=position)
    if location:
        certs = certs.filter(Employee__Location__icontains=location)
    if status:
        certs = certs.filter(Employee__Status__icontains=status)

    certs = certs.order_by(sort_by)
    params = request.GET.copy()
    if 'sort' in params:
        del params['sort']
    filter_url = params.urlencode()

    context = {
        'certs': certs,
        'filter_url': filter_url,
        'sort_by': sort_by,
        'first_name': first_name,
        'last_name': last_name,
        'position': position,
        'location': location,
        'status': status,
    }
    return render(request, 'personnel/search_certifications.html', context)

# --- EXPORTS ---
def export_employees_excel(request):
    employees = Employee.objects.all()
    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    position = request.GET.get('position', '')
    location = request.GET.get('location', '')
    status = request.GET.get('status', '')
    
    if first_name: employees = employees.filter(First_Name__icontains=first_name)
    if last_name:  employees = employees.filter(Last_Name__icontains=last_name)
    if position: employees = employees.filter(Position__icontains=position)
    if location: employees = employees.filter(Location__icontains=location)
    if status: employees = employees.filter(Status__icontains=status)
        
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Employees"

    columns = [
        'First Name', 
        'Middle Name', 
        'Last Name',
        'Status', 
        'Position', 
        'Location', 
        'Shift', 
        'Street Address', 
        'City', 
        'Prov / State', 
        'Country', 
        'Postal / Zip Code', 
        'Phone', 
        'Email'
    ]
    ws.append(columns)

    for emp in employees:
        ws.append([
            emp.First_Name,
            emp.Middle_Name,
            emp.Last_Name,
            emp.Status,
            emp.Position,
            emp.Location,
            emp.Shift,
            emp.Street_Address, 
            emp.City,
            emp.Prov_State, 
            emp.Country,
            emp.Postal_Zip, 
            emp.Phone,
            emp.Email
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Employee_Export.xlsx"'
    wb.save(response)
    return response

def export_certs_excel(request):
    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    position = request.GET.get('position', '')
    location = request.GET.get('location', '')
    status = request.GET.get('status', '')
    
    certs = EmployeeCertification.objects.all()
    
    if first_name: certs = certs.filter(Employee__First_Name__icontains=first_name)
    if last_name: certs = certs.filter(Employee__Last_Name__icontains=last_name)
    if position: certs = certs.filter(Employee__Position__icontains=position)
    if location: certs = certs.filter(Employee__Location__icontains=location)
    if status: certs = certs.filter(Employee__Status__icontains=status)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Certifications"

    ws.append(['Employee', 'Certification', 'Institution', 'Date Cert', 'Renewable', 'Renewal Cost'])

    for cert in certs:
        ws.append([str(cert.Employee), cert.Certification, cert.Institution, cert.Date_Cert, cert.Renewable, cert.Renewal_Cost])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Certification_Export.xlsx"'
    wb.save(response)
    return response

# --- CREW & SCHEDULING ---
def shift_balance_report(request):
    crew_counts = Crew.objects.annotate(emp_count=Count('employee'))
    return render(request, 'personnel/shift_balance.html', {'crew_counts': crew_counts})
    

def crew_calendar(request):
    selected_crew_id = request.GET.get('crew_id')
    crew = None
    all_months = []
    current_year = date.today().year
    
    if selected_crew_id:
        crew = get_object_or_404(Crew, id=selected_crew_id)
        all_months = crew.get_calendar_data(year=date.today().year)
        
    return render(request, 'personnel/crew_calendar.html', {
        'all_crews': Crew.objects.all(),
        'crew': crew,
        'months': all_months,
        'selected_crew_id': selected_crew_id,
        'year': current_year
    })

def shiftrotation_upload(request):
    created_ids = []
    all_patterns = ShiftPattern.objects.all()
    
    if request.method == "POST":
        post_data = request.POST.copy()
        p_name = request.POST.get('name')
        p_seq = request.POST.get('pattern_sequence')
        p_rot = request.POST.get('is_rotating') == 'on'
        
        pattern, created = ShiftPattern.objects.get_or_create(
            name=p_name,
            pattern_sequence=p_seq,
            defaults={'is_rotating': p_rot}
        )
        post_data['pattern'] = pattern.id
        post_data['province'] = 'MB'
        rotation_form = CrewShiftRotationUploadForm(post_data)
        pattern_form = ShiftPatternForm(post_data)
        
        if rotation_form.is_valid():
            with transaction.atomic():
                cov_type = rotation_form.cleaned_data['Coverage_Type']
                num_crews = pattern.get_required_crews(cov_type)
                base_start = rotation_form.cleaned_data['Start_Date']
                stagger_days = pattern.get_steps()[0]
                batch_id = uuid.uuid4()
                    
                for i in range(num_crews):
                    staggered_date = base_start + timedelta(days=stagger_days * i)
                    rotation = CrewShiftRotation.objects.create(
                        Location=rotation_form.cleaned_data['Location'],
                        Coverage_Type=cov_type,
                        Calendar_Month=rotation_form.cleaned_data['Calendar_Month'],
                        Start_Date=staggered_date,
                        pattern=pattern,
                        province=post_data['province'],
                        batch_id=batch_id,
                    )
                    created_ids.append(rotation.Shift_ID)
                messages.success(request, f"Generated {num_crews} crew schedules: {', '.join(created_ids)}")
                return redirect('personnel:personnel')
        
    else:
        rotation_form = CrewShiftRotationUploadForm()
        pattern_form = ShiftPatternForm()
        
    return render(request, "personnel/add_schedule.html", {
        'rotation_form': rotation_form,
        'pattern_form': pattern_form,
        'existing_patterns': all_patterns,
    })

def create_shift_rotation(request):
    from django.forms import modelform_factory
    PatternForm = modelform_factory(ShiftPattern, fields=['name', 'days_on', 'days_off', 'is_rotating'])

    if request.method == 'POST':
        rotation_form = CrewShiftRotationUploadForm(request.POST)
        pattern_form = PatternForm(request.POST)

        if rotation_form.is_valid() and pattern_form.is_valid():
            with transaction.atomic():
                pattern = pattern_form.save(commit=False)
                pattern.coverage_type = rotation_form.cleaned_data['Coverage_Type']
                pattern.save()

                rotation = rotation_form.save()

                Crew.objects.create(
                    location_code=rotation.Location.Facility_Code,
                    shift_letter=rotation.Shift_ID.split('-')[-1],
                    pattern=pattern,
                    start_date=rotation.Start_Date,
                )
                
            messages.success(request, f"Rotation {rotation.Shift_ID} initialized.")
            return redirect('personnel:personnel')
    else:
        rotation_form = CrewShiftRotationUploadForm()
        pattern_form = PatternForm()

    return render(request, 'personnel/create_rotation.html', {
        'rotation_form': rotation_form,
        'pattern_form': pattern_form,
    })
    
def auto_generate_crews(request):
    if request.method == 'POST':
        location = request.POST.get('location_code')
        pattern_id = request.POST.get('pattern_id')
        base_start = datetime.datetime.strptime(request.POST.get('base_start_date'), '%Y-%m-%d').date()
        
        pattern = get_object_or_404(ShiftPattern, id=pattern_id)
        stagger = pattern.get_stagger_interval()
        
        for i in range(4):
            letter = chr(65 + i)

            staggered_start = base_start + timedelta(days=stagger * i)
            
            Crew.objects.update_or_create(
                location_code=location,
                shift_letter=letter,
                defaults={
                    'pattern': pattern,
                    'start_date': staggered_start,
                    'province': 'MB'
                }
            )
        
        messages.success(request, f"Cores A-D generated for Location {location}")
        return redirect('personnel:crew_calendar')
    
def edit_schedule(request, rotation_id=None):
    # 1. SIDEBAR & FILTERING
    selected_facility_id = request.GET.get('facility_id', '').strip()
    facilities = Facility.objects.all().order_by('Facility_Code')
    
    # Get representative rows for the batch list sidebar
    schedules_query = CrewShiftRotation.objects.select_related('Location', 'pattern').order_by(
        'Location__Facility_Code', '-created_at', 'Start_Date'
    )
    if selected_facility_id:
        schedules_query = schedules_query.filter(Location_id=selected_facility_id)

    # Group into batches for the sidebar
    seen_batches = set()
    batches = []
    for s in schedules_query:
        if s.batch_id not in seen_batches:
            seen_batches.add(s.batch_id)
            # Find all rows in this batch to get the full shift list and count
            batch_rows = list(CrewShiftRotation.objects.filter(batch_id=s.batch_id).order_by('Start_Date', 'Shift_ID'))
            batches.append({
                'batch_id': s.batch_id,
                'location': s.Location,
                'coverage_type': s.Coverage_Type,
                'pattern': s.pattern,
                'province': s.province,
                'start_date': batch_rows[0].Start_Date if batch_rows else None,
                'shift_ids': [row.Shift_ID for row in batch_rows],
                'count': len(batch_rows),
                'first_rotation_id': s.id,
            })

    # 2. INITIALIZE VARIABLES FOR THE MAIN VIEW
    old_rotation = None
    old_batch = []
    new_batch = []
    replacement_options = []
    employee_preview = []
    can_remap = False
    
    # Check for target_batch_id in BOTH POST and GET
    target_batch_id = request.POST.get('target_batch_id') or request.GET.get('target_batch_id')

    # 3. IF A BATCH IS SELECTED
    if rotation_id:
        old_rotation = get_object_or_404(CrewShiftRotation.objects.select_related('Location'), pk=rotation_id)
        location = old_rotation.Location
        old_batch = list(CrewShiftRotation.objects.filter(batch_id=old_rotation.batch_id).order_by('Start_Date', 'Shift_ID'))

        # Dropdown options
        unique_batches = (
            CrewShiftRotation.objects.filter(Location=location)
            .exclude(batch_id=old_rotation.batch_id)
            .values('batch_id')
            .annotate(pattern_display=Max('pattern__name'), date_display=Min('Start_Date'))
            .order_by('-date_display')
        )
        replacement_options = []
        for batch in unique_batches:
            # 2. For each batch, fetch its IDs and join them with commas
            batch_ids = list(CrewShiftRotation.objects.filter(batch_id=batch['batch_id'])
                         .values_list('Shift_ID', flat=True))
            batch['all_ids'] = ", ".join(batch_ids)
            replacement_options.append(batch)
            
        # BUILD MAPPING (Needs to happen for both Preview and Execute)
        if target_batch_id:
            new_batch = list(CrewShiftRotation.objects.filter(batch_id=target_batch_id).order_by('Start_Date', 'Shift_ID'))
            
            def get_crew_obj(shift_id_str):
                if '-' in shift_id_str:
                    loc_part, letter_part = shift_id_str.split('-', 1)
                    return Crew.objects.filter(location_code=loc_part.strip(), shift_letter=letter_part.strip()).first()
                return None

            employee_preview = []
            
            # Map the Old Batch to the New Batch by index
            for idx, old_row in enumerate(old_batch):
                old_crew = get_crew_obj(old_row.Shift_ID)
                
                if old_crew:
                    # Match this old row to the new row at the same position
                    new_row = new_batch[idx] if idx < len(new_batch) else None
                    new_crew = get_crew_obj(new_row.Shift_ID) if new_row else None
                    
                    # Find all employees currently assigned to this OLD crew
                    # (This uses the 'crew' ForeignKey on your Employee model)
                    members = Employee.objects.filter(crew=old_crew).order_by('Last_Name')
                    
                    for emp in members:
                        employee_preview.append({
                            'employee': emp,
                            'old_crew': old_crew,
                            'new_crew': new_crew,  # This provides the "Dupont" 1800-E, etc.
                        })
            
            can_remap = bool(employee_preview) and len(new_batch) >= len(old_batch)
            
    # 4. EXECUTE SWAP (POST)
    if request.method == 'POST' and request.POST.get('action') == 'execute_swap':
        if not can_remap:
            messages.error(request, "Mapping failed. Ensure the target batch has enough crews.")
        else:
            with transaction.atomic():
                crews_to_delete = set()
                
                for entry in employee_preview:
                    emp = entry['employee']
                    target_crew = entry['new_crew']
                    old_crew = entry['old_crew']
                    
                    if target_crew:
                        Employee.objects.filter(pk=emp.pk).update(
                            crew=target_crew,
                        )
                        if old_crew:
                            crews_to_delete.add(old_crew.id)
                            
                deleted_count, _ = CrewShiftRotation.objects.filter(batch_id=old_rotation.batch_id).delete()
                
                if crews_to_delete:
                    Crew.objects.filter(id__in=crews_to_delete).delete()
                    
                messages.success(request, f"Reassigned employees and deleted {deleted_count} schedule entries.")
                return redirect('personnel:edit_schedule')

    context = {
        'batches': batches,
        'facilities': facilities,
        'selected_facility_id': selected_facility_id,
        'selected_rotation': old_rotation,
        'old_batch': old_batch,
        'new_batch': new_batch,
        'replacement_options': replacement_options,
        'target_batch_id': target_batch_id,
        'employee_preview': employee_preview,
        'can_remap': can_remap,
        'replacement_options': replacement_options,
    }
    return render(request, 'personnel/edit_schedule.html', context)