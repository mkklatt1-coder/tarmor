from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from moc.services.effval import calculate_effval
from .models import MOC, MOCQuestion, MOCQuestionResponse, MOCConsiderations, Safety, MOCConsiderations, MOCPro, MOCCon, MOCAttachment, MOCEffValPoint
from .forms import MOCQuestionResponseFormSet, AddMOCForm, MOCQuestionFormSet, SafetyForm, EditMOCForm, ConsiderationsForm, ProsFormSet, ConsFormSet,AttachmentsFormSet
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
import openpyxl

def mocs(request):
    return render(request, "moc/mocs.html")

def add_moc_view(request):
    project_id = request.GET.get('proj_id')

    if request.method == "POST":
        form = AddMOCForm(request.POST)
        if form.is_valid():
            new_moc = form.save()
            
            MOCConsiderations.objects.create(moc=new_moc)
            Safety.objects.create(moc=new_moc)
            url = reverse('moc:edit_moc', kwargs={'moc_number': new_moc.moc_number})
            if project_id:
                url += f"?proj_id={project_id}"
            return redirect(url)
    else:
        form = AddMOCForm()
    return render(request, "moc/add_moc.html", {"form": form, 'project_id': project_id})

def edit_moc_view(request, moc_number=None):
    moc = None
    considerations = None
    project_id = request.GET.get('proj_id')

    if project_id == 'None' or project_id == '':
        project_id = None

    if moc_number:
        moc = get_object_or_404(MOC, moc_number=moc_number)
        considerations, _ = MOCConsiderations.objects.get_or_create(moc=moc)

    elif request.method == 'POST' and 'lookup_number' in request.POST:
        lookup_num = request.POST.get('lookup_number')
        return redirect('moc:edit_moc', moc_number=lookup_num)

    if request.method == 'POST' and moc:
        moc_form = EditMOCForm(request.POST, instance=moc)
        cons_form = ConsiderationsForm(request.POST, instance=considerations)
        
        pros_fs = ProsFormSet(request.POST, queryset=moc.pros.all(), prefix='pros')
        cons_fs = ConsFormSet(request.POST, queryset=moc.cons.all(), prefix='cons')
        attach_fs = AttachmentsFormSet(request.POST, request.FILES, queryset=moc.attachments.all(), prefix='attachments')


        if all([moc_form.is_valid(), cons_form.is_valid(), pros_fs.is_valid(), cons_fs.is_valid(), attach_fs.is_valid()]):
            with transaction.atomic():
                moc_form.save()
                cons_form.save()

                for fs, attr in [(pros_fs, 'pros'), (cons_fs, 'cons'), (attach_fs, 'attachments')]:
                    instances = fs.save(commit=False)
                    for obj in instances:
                        obj.moc = moc
                        obj.save()
                    fs.save_m2m()
                    for obj in fs.deleted_objects:
                        obj.delete()

            messages.success(request, "MOC updated successfully.")
            print(f"DEBUG: Saving MOC {moc.moc_number} to Project ID: {project_id}")
            if project_id:
                from projects.models import Project
                Project.objects.filter(pk=project_id).update(moc_number=moc.moc_number)
                return redirect('projects:edit_project_id', pk=project_id)
            return redirect('moc:mocs')
        else:
            print("MOC Errors:", moc_form.errors)
            print("Pros Errors:", pros_fs.errors)
    else:
        moc_form = EditMOCForm(instance=moc) if moc else None
        cons_form = ConsiderationsForm(instance=considerations) if moc else None
        pros_qs = moc.pros.all() if moc else MOCPro.objects.none()
        cons_qs = moc.cons.all() if moc else MOCCon.objects.none()
        attach_qs = moc.attachments.all() if moc else MOCAttachment.objects.none()
        pros_fs = ProsFormSet(queryset=pros_qs, prefix='pros')
        cons_fs = ConsFormSet(queryset=cons_qs, prefix='cons')
        attach_fs = AttachmentsFormSet(queryset=attach_qs, prefix='attachments')

    context = {
        'moc': moc,
        'moc_form': moc_form,
        'considerations_form': cons_form,
        'pros_formset': pros_fs,
        'cons_formset': cons_fs,
        'attachments_formset': attach_fs,
        'project_id': project_id,
    }
    return render(request, 'moc/edit_moc.html', context)

def moc_effval_api(request, moc_number):
    moc = get_object_or_404(MOC, moc_number=moc_number)
    results = calculate_effval(moc)
    
    return JsonResponse({
        "effort": results.get('effort') if isinstance(results, dict) else results.effort,
        "value": results.get('value') if isinstance(results, dict) else results.value,
        "ratio": results.get('ratio') if isinstance(results, dict) else results.ratio,
    })

def moc_dashboard(request):
    points = MOCEffValPoint.objects.select_related('moc').order_by('-ratio')
    
    return render(request, 'moc/moc_dashboard.html', {
        'dashboard_data': points
    })

def moc_dashboard_api(request):
    points = MOCEffValPoint.objects.select_related('moc').order_by('-ratio')
    
    dashboard_data = []
    for p in points:
        dashboard_data.append({
            'moc': p.moc,
            'effort': p.effort,
            'value': p.value,
            'ratio': p.ratio,
        })
        
    return render(request, 'moc/moc_dashboard.html', {
        'dashboard_data': dashboard_data
    })

def moc_questions(request):
    selected_section = request.GET.get('section_filter')
    
    if selected_section:
        queryset = MOCQuestion.objects.filter(section=selected_section).order_by('order')
    else:
        queryset = MOCQuestion.objects.none()

    if request.method == "POST":
        formset = MOCQuestionFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Question list updated successfully.")
            return redirect(f"{reverse('moc:mocs')}?section_filter={selected_section}")
    else:
        formset = MOCQuestionFormSet(queryset=queryset)
        
    sections = MOCQuestion.objects.values_list('section', flat=True).distinct()

    return render(request, "moc/moc_questions.html", {
        "formset": formset,
        "sections": sections,
        "selected_section": selected_section
    })

def moc_questions_response(request, moc_number, section):
    moc = get_object_or_404(MOC, moc_number=moc_number)
    
    master_questions = MOCQuestion.objects.filter(section=section)
    for q in master_questions:
        MOCQuestionResponse.objects.get_or_create(moc=moc, question=q)

    queryset = MOCQuestionResponse.objects.filter(
        moc=moc, 
        question__section=section
    ).order_by('question__order')

    if request.method == "POST":
        formset = MOCQuestionResponseFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            return redirect('moc:edit_moc', moc_number=moc.moc_number)
        else:
            print(formset.errors)
    else:
        formset = MOCQuestionResponseFormSet(queryset=queryset)

    return render(request, "moc/moc_question_resp.html", {
        "moc": moc,
        "formset": formset,
        "section": section,
    })

def safety_health_view(request, moc_number):
    moc = get_object_or_404(MOC, moc_number=moc_number)
    safety, created = Safety.objects.get_or_create(moc=moc)
    questions = MOCQuestion.objects.filter(section="safety").order_by("order")
    for q in questions:
        MOCQuestionResponse.objects.get_or_create(
            moc=moc,
            question=q
        )
    question_queryset = MOCQuestionResponse.objects.filter(
        moc=moc,
        question__section="safety"
    ).order_by("question__order")
    if request.method == "POST":
        safety_form = SafetyForm(request.POST, instance=safety)
        question_formset = MOCQuestionResponseFormSet(
            request.POST,
            queryset=question_queryset
        )
        if safety_form.is_valid() and question_formset.is_valid():
            safety_form.save()
            question_formset.save()
            return redirect("moc:edit_moc", moc_number=moc.moc_number)
    else:
        safety_form = SafetyForm(instance=safety)
        question_formset = MOCQuestionResponseFormSet(queryset=question_queryset)
    return render(request, "moc/safety_health.html", {
        "moc": moc,
        "safety": safety,
        "safety_form": safety_form,
        "question_formset": question_formset,
    })

def upload_attachment_api(request, moc_number):
    if request.method == 'POST':
        moc = get_object_or_404(MOC, moc_number=moc_number)
        file = request.FILES.get('file')
        desc = request.POST.get('description', '')
        
        attachment = MOCAttachment.objects.create(
            moc=moc, 
            file=file, 
            description=desc
        )
        
        return JsonResponse({
            'success': True, 
            'url': attachment.file.url
        })
    return JsonResponse({'success': False}, status=400)

def moc_search_list(request):
    mocs = MOC.objects.all()

    moc_num_query = request.GET.get('moc_num')
    title_query = request.GET.get('title_keyword')

    if moc_num_query:
        mocs = mocs.filter(moc_number__icontains=moc_num_query)
    
    if title_query:
        mocs = mocs.filter(title__icontains=title_query)

    sort_by = request.GET.get('sort', 'moc_number')
    direction = request.GET.get('dir', 'asc')

    if direction == 'desc':
        mocs = mocs.order_by(f'-{sort_by}')
    else:
        mocs = mocs.order_by(sort_by)

    all_moc_nums = MOC.objects.values_list('moc_number', flat=True).distinct()
    all_titles = MOC.objects.values_list('title', flat=True).distinct()

    if 'export' in request.GET:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "MOC Export"
        headers = ['MOC', 'Title', 'Created', 'Completed', 'Status']
        ws.append(headers)

        for moc in mocs:
            ws.append([
                moc.moc_number,
                moc.title,
                moc.date_created.strftime('%Y-%m-%d') if moc.date_created else '',
                moc.date_completed.strftime('%Y-%m-%d') if moc.date_completed else '',
                moc.status
            ])
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename=MOC_Export.xlsx'
        wb.save(response)
        return response

    return render(request, 'moc/search_mocs.html', {
        'mocs': mocs,
        'all_moc_nums': all_moc_nums,
        'all_titles': all_titles,
        'sort_by': sort_by,
        'direction': direction,
    })

def export_moc_rankings_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "MOC Effort-Value Rankings"

    headers = ['MOC Number', 'Title', 'Status', 'Effort', 'Value', 'V/E Ratio', 'Rank']
    ws.append(headers)

    rankings = MOCEffValPoint.objects.select_related('moc').order_by('-ratio')

    for index, item in enumerate(rankings, start=1):
        ws.append([
            item.moc.moc_number,
            item.moc.title,
            item.moc.status,
            item.effort,
            item.value,
            item.ratio,
            index
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="MOC_Rankings.xlsx"'
    
    wb.save(response)
    return response