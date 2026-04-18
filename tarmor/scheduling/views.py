from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import WorkWeek, Schedule, WorkOrder, ScheduleSnapshot, Garage

def scheduling (request):
    return render(request, 'scheduling/scheduling.html')

def scheduling_view(request):
    week_num = request.GET.get("week")
    garage_id = request.GET.get("garage")
    weeks = WorkWeek.objects.all().order_by("week_number")
    garages = Garage.objects.all()
    selected_week = WorkWeek.objects.filter(week_number=week_num).first()
    selected_garage = Garage.objects.filter(id=garage_id).first()
    work_orders = WorkOrder.objects.filter(
        planned_start__range=(selected_week.start_date, selected_week.end_date),
        responsible_garage=selected_garage,
        completion_date__isnull=True,
        job_status__in=["Waiting to Schedule", "Reschedule", "Execution"],
    ).order_by("planned_start")
    # compute daily totals
    daily_hours = {day: 0 for day in range(7)}
    for wo in work_orders:
        if wo.planned_start:
            offset = (wo.planned_start - selected_week.start_date).days
            if 0 <= offset < 7:
                daily_hours[offset] += float(wo.estimated_hours)
    return render(
        request,
        "scheduling/schedule.html",
        {
            "weeks": weeks,
            "garages": garages,
            "selected_week": selected_week,
            "selected_garage": selected_garage,
            "work_orders": work_orders,
            "daily_hours": daily_hours,
        },
    )
@require_POST
def update_workorder_date(request, pk):
    """AJAX inline edit for planned start date."""
    wo = get_object_or_404(WorkOrder, pk=pk)
    date_str = request.POST.get("planned_start")
    if date_str:
        wo.planned_start = date_str
        wo.save()
    return JsonResponse({"ok": True, "planned_start": wo.planned_start})
def lock_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    if not schedule.locked:
        schedule.lock()
        # snapshot
        eligible_wos = WorkOrder.objects.filter(
            planned_start__range=(schedule.week.start_date, schedule.week.end_date),
            responsible_garage=schedule.responsible_garage,
        )
        for wo in eligible_wos:
            ScheduleSnapshot.objects.create(
                schedule=schedule,
                work_order=wo,
                planned_start_snapshot=wo.planned_start,
                estimated_hours_snapshot=wo.estimated_hours,
                job_status_snapshot=wo.job_status,
                completion_date_snapshot=wo.completion_date,
            )
    return redirect("scheduling:schedule", week=schedule.week.week_number)