from django.contrib import messages
from django import forms
from django.http import HttpResponse
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory, modelform_factory
from django.db.models import Count, Max, Min, Q, Value
from django.db.models.functions import Concat
from .models import Employee, EmployeeCertification, Crew, CrewShiftRotation, ShiftPattern
from .forms import (NewEmployeeForm, CertificationFormSet, EmployeeCertificationForm, CrewShiftRotationUploadForm,
    ShiftPatternForm, ReplaceScheduleBatchForm)
import openpyxl, datetime, calendar, holidays, uuid
from datetime import date, timedelta, datetime, time
from facilities.models import Facility

def personnel(request):
    return render(request, 'personnel/personnel.html')

def add_employee(request):
    employee = Employee()
    if request.method == 'POST':
        new_emp_form = NewEmployeeForm(request.POST, request.FILES, instance=employee)
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
    full_name_query = request.GET.get('employee_search', '').strip()

    if full_name_query:
        parts = full_name_query.split()
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]
            employee = Employee.objects.filter(
                First_Name__iexact=first,
                Last_Name__iexact=last
            ).first()
        else:
            employee = Employee.objects.filter(
                Q(First_Name__icontains=full_name_query) |
                Q(Last_Name__icontains=full_name_query)
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
        form = NewEmployeeForm(request.POST, request.FILES, instance=employee)
        formset = CertificationFormSet(request.POST, instance=employee, prefix='cert')
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('personnel:personnel')
    else:
        form = NewEmployeeForm(instance=employee)
        formset = CertificationFormSet(instance=employee, prefix='cert')

    all_employees = Employee.objects.all().only('First_Name', 'Last_Name').order_by('First_Name')

    return render(request, 'personnel/edit_employee.html', {
        'new_emp_form': form,
        'cert_formset': formset,
        'employee': employee,
        'all_employees': all_employees,
        'full_name_query': full_name_query
    })
    
def search_employee(request):
    employee_search = request.GET.get('employee_search', '').strip()
    position = request.GET.get('position', '').strip()
    crew_query = request.GET.get('crew', '').strip()
    status = request.GET.get('status', '').strip()

    employees = Employee.objects.all().annotate(
        combined_crew_name=Concat('crew__location_code', Value('-'), 'crew__shift_letter')
    )

    if employee_search:
        parts = employee_search.split()
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]
            employees = employees.filter(
                (Q(First_Name__icontains=first) & Q(Last_Name__icontains=last)) |
                (Q(First_Name__icontains=last) & Q(Last_Name__icontains=first))
            )
        else:
            employees = employees.filter(
                Q(First_Name__icontains=employee_search) |
                Q(Last_Name__icontains=employee_search)
            )

    if position:
        employees = employees.filter(Position__icontains=position)
    if crew_query:
        employees = employees.filter(combined_crew_name__icontains=crew_query)
    if status:
        employees = employees.filter(Status__icontains=status)
    
    sort_by = request.GET.get('sort', 'Last_Name')
    is_descending = sort_by.startswith('-')
    clean_sort_key = sort_by.lstrip('-')

    sort_mapping = {
        'First_Name': 'First_Name',
        'Middle_Name': 'Middle_Name',
        'Last_Name': 'Last_Name',
        'Status': 'Status',
        'Position': 'Position',
        'crew': 'combined_crew_name',
        'Street_Address': 'Street_Address',
        'City': 'City',
        'Prov_State': 'Prov_State',
        'Country': 'Country',
        'Postal_Zip': 'Postal_Zip',
        'Phone': 'Phone',
        'Email': 'Email',
    }

    if clean_sort_key in sort_mapping:
        db_field = sort_mapping[clean_sort_key]
        order_field = f"-{db_field}" if is_descending else db_field
        employees = employees.order_by(order_field)
    else:
        employees = employees.order_by('Last_Name')

    params = request.GET.copy()
    if 'sort' in params:
        del params['sort']
    filter_url = params.urlencode()

    all_employees = Employee.objects.all().only('First_Name', 'Last_Name').order_by('First_Name')
    all_positions = Employee.objects.exclude(Position__isnull=True).values_list('Position', flat=True).distinct().order_by('Position')
    all_statuses = Employee.objects.exclude(Status__isnull=True).values_list('Status', flat=True).distinct().order_by('Status')
    all_crews = (
        Employee.objects.exclude(crew__location_code__isnull=True)
        .annotate(crew_str=Concat('crew__location_code', Value('-'), 'crew__shift_letter'))
        .values_list('crew_str', flat=True)
        .distinct()
        .order_by('crew_str')
    )

    context = {
        'employees': employees,
        'filter_url': filter_url,
        'sort': sort_by,
        'all_employees': all_employees,
        'all_positions': all_positions,
        'all_crews': all_crews,
        'all_statuses': all_statuses,
        'employee_search_val': employee_search,
        'position_val': position,
        'crew_val': crew_query,
        'status_val': status,
    }

    return render(request, 'personnel/search_employee.html', context)

def search_certifications(request):
    employee_search = request.GET.get('employee_search', '').strip()
    position = request.GET.get('position', '').strip()
    location_name = request.GET.get('location', '').strip()
    status = request.GET.get('status', '').strip()

    certs = EmployeeCertification.objects.select_related('Employee', 'Employee__crew').all()

    if employee_search:
        parts = employee_search.split()
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]
            
            certs = certs.filter(
                (Q(Employee__First_Name__icontains=first) & Q(Employee__Last_Name__icontains=last)) |
                (Q(Employee__First_Name__icontains=last) & Q(Employee__Last_Name__icontains=first))
            )
        else:
            certs = certs.filter(
                Q(Employee__First_Name__icontains=employee_search) |
                Q(Employee__Last_Name__icontains=employee_search)
            )
    
    if position:
        certs = certs.filter(Employee__Position__icontains=position)

    if position:
        certs = certs.filter(Employee__Position__icontains=position)
        
    if location_name:
        facility = Facility.objects.filter(Facility_Name__iexact=location_name).first()
        if facility:
            certs = certs.filter(Employee__crew__location_code=facility.Facility_Code)
        else:
            certs = certs.none()
            
    if status:
        certs = certs.filter(Employee__Status__icontains=status)

    sort_by = request.GET.get('sort', 'Employee__Last_Name')
    is_descending = sort_by.startswith('-')
    clean_sort_key = sort_by.lstrip('-')

    sort_mapping = {
        'Employee__First_Name': 'Employee__First_Name',
        'Employee__Middle_Name': 'Employee__Middle_Name',
        'Employee__Last_Name': 'Employee__Last_Name',
        'Employee__Status': 'Employee__Status',
        'Employee__Position': 'Employee__Position',
        'Employee__Location': 'Employee__crew__location_code',
        'Certification': 'Certification',
        'Institution': 'Institution',
        'Date_Cert': 'Date_Cert',
        'Renewable': 'Renewable',
        'Renewal_Cost': 'Renewal_Cost',
    }

    if clean_sort_key in sort_mapping:
        db_field = sort_mapping[clean_sort_key]
        certs = certs.order_by(f"-{db_field}" if is_descending else db_field)
    else:
        certs = certs.order_by('Employee__Last_Name')

    params = request.GET.copy()
    if 'sort' in params:
        del params['sort']
    filter_url = params.urlencode()

    all_employees = Employee.objects.all().only('First_Name', 'Last_Name').order_by('First_Name')
    all_positions = Employee.objects.exclude(Position__isnull=True).values_list('Position', flat=True).distinct().order_by('Position')
    all_statuses = Employee.objects.exclude(Status__isnull=True).values_list('Status', flat=True).distinct().order_by('Status')
    all_locations = Facility.objects.all().values_list('Facility_Name', flat=True).distinct().order_by('Facility_Name')

    return render(request, 'personnel/search_certifications.html', {
        'certs': certs,
        'filter_url': filter_url,
        'sort': sort_by,
        'all_employees': all_employees,
        'all_positions': all_positions,
        'all_locations': all_locations,
        'all_statuses': all_statuses,
        'employee_search_val': employee_search,
        'position_val': position,
        'location_val': location_name,
        'status_val': status,
    })

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
        location_code = request.POST.get('location_code')
        pattern_id = request.POST.get('pattern_id')
        
        # Parse user's chosen start date and time
        user_date = datetime.strptime(request.POST.get('base_start_date'), '%Y-%m-%d').date()
        user_time = datetime.strptime(request.POST.get('shift_start'), '%H:%M:%S').time()
        user_hrs = int(request.POST.get('hrs_per_shift', 12))
        
        pattern = get_object_or_404(ShiftPattern, id=pattern_id)
        stagger = pattern.get_stagger_interval()
        batch_id = uuid.uuid4()

        for i in range(4):
            letter = chr(69 + i)
            date_offset = stagger if i % 2 != 0 else 0
            current_date = user_date + timedelta(days=date_offset)

            if i >= 2:
                
                temp_dt = datetime.combine(date.today(), user_time) + timedelta(hours=user_hrs)
                current_time = temp_dt.time()
            else:
                current_time = user_time

            with transaction.atomic():
                rotation = CrewShiftRotation.objects.create(
                    Location=Location.objects.get(Facility_Code=location_code),
                    Coverage_Type="24H",
                    Start_Date=current_date,
                    shift_start=current_time,
                    hrs_per_shift=user_hrs,
                    pattern=pattern,
                    province='MB',
                    batch_id=batch_id
                )

                Crew.objects.update_or_create(
                        location_code=location_code,
                        shift_letter=letter,
                        defaults={
                            'rotation': rotation,
                            'pattern': pattern,
                            'start_date': current_date,
                        }
                    )
            
        messages.success(request, f"Cores generated for Location {location}")
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