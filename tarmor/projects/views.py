from django.shortcuts import render, get_object_or_404, redirect
from .models import Project, ProjectAttachment, ProjectBudget, ProjectFinancial, ProjectStep, CompanyBudget
from .forms import (ProjectForm, StepFormSet, AttachmentFormSet, DelayFormSet, BudgetFormSet, ProjectNoteFormSet, 
                    ProjectLessonFormSet, FinancialFormSet, ProjectTasksFormSet, ProjectPlanningForm)
from django.contrib import messages
from django.db.models import Sum
from django.forms import modelformset_factory
import datetime
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
import openpyxl
from django.http import HttpResponse
from django.db.models import Q
from .models import Project
import json

def projects(request):
    return render(request, 'projects/projects.html')

def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            new_project = form.save()
            return redirect('projects:edit_project_id', pk=new_project.id)
        else:
            print(form.errors)
    else:
        form = ProjectForm()
    return render(request, 'projects/create_project.html', {'form': form})

def edit_project(request, pk=None):
    
    if request.method == 'POST' and 'lookup_number' in request.POST:
        num = request.POST.get('lookup_number')
        found = Project.objects.filter(project_number=num).first()
        if found:
            return redirect('projects:edit_project_id', pk=found.id)
        messages.error(request, f"Project {num} not found.")
        return redirect('projects:edit_project')
    
    project = get_object_or_404(Project, pk=pk) if pk else None
    po_total = 0

    if project:
        po_total = project.purchase_orders.aggregate(Sum('grand_total'))['grand_total__sum'] or 0

        if project.uom and project.uom.lower() == 'years' and project.execution_time > 0:
            current_year = datetime.date.today().year
            for i in range(project.execution_time):
                target_year = current_year + i
                ProjectBudget.objects.get_or_create(project=project, year=target_year)

    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        budget_fs = BudgetFormSet(request.POST, instance=project, prefix='budget')
        attach_fs = AttachmentFormSet(request.POST, request.FILES, instance=project, prefix='attach')
        steps_fs = StepFormSet(request.POST, instance=project, prefix='steps')
        delays_fs = DelayFormSet(request.POST, instance=project, prefix='delays')

        if all([form.is_valid(), attach_fs.is_valid(), steps_fs.is_valid(), delays_fs.is_valid(), budget_fs.is_valid()]):
            project = form.save()
            attach_fs.save()
            steps_fs.save()
            delays_fs.save()
            budget_fs.save()
            project.update_totals()
            messages.success(request, 'Project updated successfully.')
            action = request.POST.get('form_action')

            if action == 'save_exit':
                return redirect('projects:projects')
            else:
                return redirect('projects:edit_project_id', pk=project.id)
        else:
            print(f"DEBUG: Processing Save for PK: {pk}")
            print(form.errors)
    else:
        form = ProjectForm(instance=project)
        attach_fs = AttachmentFormSet(instance=project, prefix='attach')
        steps_fs = StepFormSet(instance=project, prefix='steps')
        delays_fs = DelayFormSet(instance=project, prefix='delays')
        budget_fs = BudgetFormSet(instance=project, prefix='budget')

    return render(request, 'projects/edit_project.html', {
        'form': form, 
        'proj': project,
        'po_total': po_total,
        'budget_formset': budget_fs,
        'attachments_formset': attach_fs,
        'steps_formset': steps_fs,
        'delays_formset': delays_fs,
    })

def add_attachment(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        file = request.FILES.get('file')
        if file:
            ProjectAttachment.objects.create(project=project, name=name, file=file)
            messages.success(request, "Attachment added.")
    return redirect('projects:edit_project_id', pk=project_id)

def update_totals(self):
    from django.db.models import Sum
    self.budget = self.budgets.aggregate(Sum('allocated_budget'))['allocated_budget__sum'] or 0
    self.spend = self.purchase_orders.aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    self.remaining = self.budget - self.spend
    self.save()

def project_notes(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    
    if request.method == 'POST':
        formset = ProjectNoteFormSet(request.POST, request.FILES, instance=project, form_kwargs={'project': project})
        for form in formset:
            form.fields['step'].queryset = project.steps.all()

        if formset.is_valid():
            formset.save()
            return redirect('projects:edit_project_id', pk=project.id)
    else:
        formset = ProjectNoteFormSet(instance=project)
        for form in formset:
            form.fields['step'].queryset = project.steps.all()

    return render(request, 'projects/project_notes.html', {
        'project': project,
        'formset': formset,
    })

def project_lessons(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    
    if request.method == 'POST':
        formset = ProjectLessonFormSet(request.POST, request.FILES, instance=project, form_kwargs={'project': project})
        for form in formset:
            form.fields['step'].queryset = project.steps.all()

        if formset.is_valid():
            formset.save()
            return redirect('projects:edit_project_id', pk=project.id)
    else:
        formset = ProjectLessonFormSet(instance=project)
        for form in formset:
            form.fields['step'].queryset = project.steps.all()

    return render(request, 'projects/lessons_learned.html', {
        'project': project,
        'formset': formset,
    })

def project_financials(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    
    valid_years = list(project.budgets.values_list('year', flat=True))

    if valid_years:
        project.financials.exclude(year__in=valid_years).delete()

        for yr in valid_years:
            ProjectFinancial.objects.get_or_create(project=project, year=yr)
            
    if request.method == 'POST':
        formset = FinancialFormSet(request.POST, instance=project)
        if formset.is_valid():
            formset.save()
            project.update_totals()
            return redirect('projects:edit_project_id', pk=project.id)
        else:
            print("Financial Formset Errors:", formset.errors)
    else:
        formset = FinancialFormSet(
            instance=project, 
            queryset=ProjectFinancial.objects.filter(project=project).order_by('year')
        )
    months = range(1, 13)
    
    return render(request, 'projects/project_financial.html', {
        'project': project,
        'formset': formset,
        'months': months,
    })

def project_gantt(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    steps = project.steps.all().order_by('start_date')
    
    if not steps:
        return redirect('projects:edit_project_id', pk=project.id)

    start_bound = min(s.start_date for s in steps)
    start_bound -= timedelta(days=start_bound.weekday()) 
    end_date = max(s.get_final_date() for s in steps) + timedelta(days=14)
    
    week_headers = []
    curr = start_bound
    while curr <= end_date:
        week_headers.append(curr)
        curr += timedelta(days=7)
    
    total_weeks = len(week_headers)
    today = date.today()
    chart_data = []

    for s in steps:
        start_col = (s.start_date - start_bound).days / 7
        planned_width = s.get_duration_days() / 7
        delay_width = s.get_delay_days() / 7
        
        is_overdue = today > s.get_final_date() and s.status.lower() != 'complete'
        bar_color = "#00009c"
        if s.status.lower() == 'complete': bar_color = "green"
        elif is_overdue: bar_color = "red"

        chart_data.append({
            'step': s,
            'start_col': start_col + 2,
            'planned_width': max(planned_width, 0.2),
            'delay_width': delay_width,
            'color': bar_color,
        })

    return render(request, 'projects/project_gantt.html', {
        'project': project,
        'week_headers': week_headers,
        'total_weeks': total_weeks,
        'chart_data': chart_data,
    })

def project_tasks(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    
    if request.method == 'POST':
        formset = ProjectTasksFormSet(request.POST, request.FILES, instance=project, form_kwargs={'project': project})
        for form in formset:
            form.fields['step'].queryset = project.steps.all()

        if formset.is_valid():
            formset.save()
            return redirect('projects:edit_project_id', pk=project.id)
    else:
        formset = ProjectTasksFormSet(instance=project)
        for form in formset:
            form.fields['step'].queryset = project.steps.all()

    return render(request, 'projects/project_tasks.html', {
        'project': project,
        'formset': formset,
    })

def search_projects(request):
    projects = Project.objects.all() 
    
    proj_num = request.GET.get('proj_num')
    keyword = request.GET.get('title_keyword')
    
    if proj_num:
        projects = projects.filter(project_number__icontains=proj_num)
    if keyword:
        projects = projects.filter(
            Q(description__icontains=keyword) | Q(project_number__icontains=keyword)
        )

    sort_by = request.GET.get('sort', 'project_number')
    direction = request.GET.get('dir', 'asc')
    
    sort_mapping = {
        'project_number': 'project_number',
        'title': 'description',
        'status': 'status',
    }
    
    order_field = sort_mapping.get(sort_by, 'project_number')
    if direction == 'desc':
        order_field = f"-{order_field}"
    
    projects = projects.order_by(order_field)

    context = {
        'projects': projects,
        'all_proj_nums': Project.objects.values_list('project_number', flat=True).distinct(),
        'all_titles': Project.objects.values_list('description', flat=True).distinct(),
        'sort_by': sort_by,
        'direction': direction,
    }

    if request.GET.get('export') == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Project Search Results"

        headers = ['Project #', 'Description', 'MOC #', 'V/E Ratio', 'Status', '% Complete']
        ws.append(headers)

        for proj in projects:
            ve_ratio = proj.moc.ve_ratio if hasattr(proj, 'moc') and proj.moc else "-"

            ws.append([
                proj.project_number,
                proj.description,
                proj.moc_number,
                proj.moc.ve_ratio,
                proj.status,
                proj.completion_percentage
            ])

        response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        response['Content-Disposition'] = 'attachment; filename="Project_Export.xlsx"'
        
        wb.save(response)
        return response
    
    context = {
        'projects': projects,
        'all_proj_nums': Project.objects.values_list('project_number', flat=True).distinct(),
        'all_titles': Project.objects.values_list('description', flat=True).distinct(),
        'sort_by': request.GET.get('sort', 'project_number'),
        'direction': request.GET.get('dir', 'asc'),
    }
    
    return render(request, 'projects/search_projects.html', context)

def project_dashboard(request):
    selected_year = request.GET.get('year')
    selected_status = request.GET.get('status')
    show_complete = request.GET.get('show_complete') == 'true'

    this_year = datetime.date.today().year
    dynamic_years = [y for y in range(this_year - 5, this_year + 6)]

    projects = Project.objects.all().prefetch_related('steps', 'budgets', 'purchase_orders', 'financials')
    if not show_complete:
        projects = projects.exclude(status='Complete')
    if selected_status:
        projects = projects.filter(status=selected_status)
    
    total_budget = 0
    total_spend = 0
    total_cost_co = 0
    total_cash_co = 0

    labels, planned, spend, cost, cash = [], [], [], [], []
    dashboard_data = []

    for p in projects:
        total_delay = p.delays.aggregate(Sum('time_requirement'))['time_requirement__sum'] or 0
        execution_days = p.execution_time * 365 if p.uom == 'Years' else p.execution_time
        is_high_risk = (total_delay > (execution_days * 0.1))

        if selected_year:
            fin = p.financials.filter(year=selected_year).first()
            s_val = float(p.purchase_orders.filter(date__year=selected_year).aggregate(Sum('grand_total'))['grand_total__sum'] or 0.0)
            p_val = float(fin.planned_total) if fin else 0.0
            c_val = float(fin.cost_total) if fin else 0.0
            ca_val = float(fin.cash_total) if fin else 0.0
            c_co = float(fin.cost_carryover) if fin else 0.0
            ca_co = float(fin.cash_carryover) if fin else 0.0
        else:
            s_val = float(p.spend)
            p_val = float(p.budget)
            c_val = float(sum(f.cost_total for f in p.financials.all()))
            ca_val = float(sum(f.cash_total for f in p.financials.all()))
            c_co = float(sum(f.cost_carryover for f in p.financials.all()))
            ca_co = float(sum(f.cash_carryover for f in p.financials.all()))

        total_budget += p_val
        total_spend += s_val
        total_cost_co += c_co
        total_cash_co += ca_co

        labels.append(p.project_number)
        planned.append(p_val)
        spend.append(s_val)
        cost.append(c_val)
        cash.append(ca_val)
        
        dashboard_data.append({
            'obj': p,
            'is_high_risk': is_high_risk,
            'duration_type': 'M' if (p.execution_time > 1 and p.uom == 'Years') else 'S',
            'cost_co': c_co,
            'cash_co': ca_co,
        })

    all_steps = ProjectStep.objects.all()
    if all_steps:
        start_date = min(s.start_date for s in all_steps)
        start_date = start_date.replace(day=1)
    else:
        start_date = date.today().replace(day=1)

    context = {
        'dashboard_data': dashboard_data,
        'total_budget': total_budget,
        'total_spend': total_spend,
        'total_cost_co': total_cost_co,
        'total_cash_co': total_cash_co,
        'years': dynamic_years,
        'statuses': Project.STATUS_CHOICES,
        'selected_year': selected_year,
        'selected_status': selected_status,
        'show_complete': show_complete,
        'fin_json': json.dumps({'labels': labels, 'planned': planned, 'spend': spend, 'cost': cost, 'cash': cash})
    }
    return render(request, 'projects/dashboard.html', context)

def project_planning(request):
    selected_year = request.GET.get('year', '')
    selected_status = request.GET.get('status', '')
    show_complete = request.GET.get('show_complete') == 'true'

    if request.method == 'POST' and 'set_comp_budget' in request.POST:
            if selected_year and selected_year.isdigit():
                comp_budget_obj, _ = CompanyBudget.objects.get_or_create(year=selected_year)
                comp_budget_obj.amount = request.POST.get('set_comp_budget', 0)
                comp_budget_obj.save()
                return redirect(f"{request.path}?year={selected_year}&status={selected_status}")

    comp_budget_amount = 0
    if selected_year and selected_year.isdigit():
        comp_budget_obj = CompanyBudget.objects.filter(year=selected_year).first()
        comp_budget_amount = comp_budget_obj.amount if comp_budget_obj else 0
    else:
        comp_budget_amount = CompanyBudget.objects.aggregate(Sum('amount'))['amount__sum'] or 0

    projects_qs = Project.objects.all()
    if not show_complete:
        projects_qs = projects_qs.exclude(status='Complete')
    if selected_status:
        projects_qs = projects_qs.filter(status=selected_status)

    if selected_year and selected_year.isdigit():
        table_qs = projects_qs.filter(Q(start_year=selected_year) | Q(start_year__isnull=True))
        total_assigned_value = Project.objects.filter(start_year=selected_year).aggregate(Sum('budget'))['budget__sum'] or 0
    else:
        table_qs = projects_qs
        total_assigned_value = Project.objects.aggregate(Sum('budget'))['budget__sum'] or 0
    

    PlanFormSet = modelformset_factory(Project, form=ProjectPlanningForm, extra=0)
    if request.method == 'POST' and 'form-TOTAL_FORMS' in request.POST:
        formset = PlanFormSet(request.POST, queryset=table_qs)
        if formset.is_valid():
            formset.save()
            return redirect(request.get_full_path())
    else:
        formset = PlanFormSet(queryset=table_qs)

    context = {
        'formset': formset,
        'years': range(datetime.date.today().year - 6, datetime.date.today().year + 6),
        'selected_year': selected_year,
        'selected_status': selected_status,
        'show_complete': show_complete,
        'comp_budget': comp_budget_amount,
        'total_assigned': total_assigned_value,
        'statuses': Project.STATUS_CHOICES,
    }
    return render(request, 'projects/project_planning.html', context)