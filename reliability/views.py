import json
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Q, Max, Min, Count, Avg
from datetime import date
from decimal import Decimal
from collections import defaultdict
from equipment.models import Equipment, AssetType, EQ_Type, Meter
from meters.models import MeterReading
from .models import RebuildPlanRow
from django.http import HttpResponse
from .utils import get_combined_priority_score

def reliability(request):
    return render(request, 'reliability/reliability.html')

def calculate_next_intervention(eq, target_year, current_year):
    uom_oh = str(eq.oh_uom or '').strip()
    uom_eol = str(eq.eol_uom or '').strip()
    is_calendar = (uom_oh == 'Calendar Years' or uom_eol == 'Calendar Years')

    if not eq.Overhaul_Period or not eq.End_of_Life:
        return None
        
    overhaul_period = eq.Overhaul_Period
    end_of_life = eq.End_of_Life
    overhaul_value = eq.Overhaul_Value if eq.Overhaul_Value else Decimal('0.00')
    replacement_value = eq.Equipment_Value if eq.Equipment_Value else Decimal('0.00')
    
    commission_year = eq.Commissioning_Date.year if eq.Commissioning_Date else current_year
    years_since_commission = target_year - commission_year
    
    if years_since_commission < 0:
        return None

    if is_calendar:
        if years_since_commission == end_of_life:
            return {'type': 'Replace', 'cost': replacement_value, 'label': f"RP \${int(replacement_value):,}"}
        
        if years_since_commission > 0 and years_since_commission < end_of_life and (years_since_commission % overhaul_period == 0):
            cycle_num = int(years_since_commission / overhaul_period)
            return {'type': 'Rebuild', 'cost': overhaul_value, 'label': f"OH{cycle_num} \${int(overhaul_value):,}"}
            
        eq.current_meter_value_display = "Calendar Based"
        return None

    target_meter = Meter.objects.filter(equipment_id=eq.id, meter_type=uom_oh).first()
    if not target_meter:
        target_meter = Meter.objects.filter(equipment_id=eq.id).first()

    current_hours = 0
    avg_yearly_hours = 2000 if 'Hours' in uom_oh else 12000
    
    if target_meter:
        meter_readings_query = MeterReading.objects.filter(Equipment_id=eq.id, Meter_Type_id=target_meter.id)
        latest_reading = meter_readings_query.order_by('-Date', '-id').first()
        if latest_reading:
            if latest_reading.Total_Meter_Value is not None:
                current_hours = latest_reading.Total_Meter_Value
            elif latest_reading.Meter_Reading is not None:
                current_hours = latest_reading.Meter_Reading

        sorted_readings = meter_readings_query.order_by('Date')
        if sorted_readings.count() >= 2:
            first, last = sorted_readings.first(), sorted_readings.last()
            if first.Date and last.Date and last.Date > first.Date:
                days_diff = (last.Date - first.Date).days
                first_val = first.Total_Meter_Value if first.Total_Meter_Value is not None else 0
                last_val = last.Total_Meter_Value if last.Total_Meter_Value is not None else 0
                hours_diff = last_val - first_val
                if days_diff > 30 and hours_diff > 0:
                    avg_yearly_hours = max(500, (hours_diff / days_diff) * 365.25)


    unit_label = "HRS" if 'Hours' in uom_oh else "KMS"
    eq.current_meter_value_display = f"{int(current_hours):,} {unit_label}" if current_hours > 0 else f"0 {unit_label}"

    years_from_now_start = max(0, target_year - current_year)
    years_from_now_end = max(0, (target_year + 1) - current_year)
    
    hours_at_start_of_year = current_hours + (years_from_now_start * avg_yearly_hours)
    hours_at_end_of_year = current_hours + (years_from_now_end * avg_yearly_hours)

    if hours_at_start_of_year < end_of_life <= hours_at_end_of_year:
        return {'type': 'Replace', 'cost': replacement_value, 'label': f"RP \${int(replacement_value):,}"}

    max_possible_overhauls = int(end_of_life / overhaul_period) + 1
    for cycle in range(1, max_possible_overhauls):
        interval_threshold = overhaul_period * cycle
        if interval_threshold >= end_of_life:
            break
            
        if hours_at_start_of_year < interval_threshold <= hours_at_end_of_year:
            return {'type': 'Rebuild', 'cost': overhaul_value, 'label': f"OH{cycle} \${int(overhaul_value):,}"}

    return None

def rebuild_replacement_plan(request):
    current_year = date.today().year
    five_year_timeline = [current_year + i for i in range(6)]

    asset_type_val = request.GET.get('asset_type', '').strip()
    eq_type_val = request.GET.get('eq_type', '').strip()
    eq_num_val = request.GET.get('equipment_number', '').strip()
    sort_by = request.GET.get('sort', 'equipment_number')

    if request.method == 'POST':
        with transaction.atomic():
            plan_ids = request.POST.getlist('plan_row_id')
            for p_id in plan_ids:
                plan_row = RebuildPlanRow.objects.get(id=p_id)
                
                mod_yr = request.POST.get(f'mod_year_{p_id}', '').strip()
                proj_num = request.POST.get(f'proj_num_{p_id}', '').strip()
                approved = request.POST.get(f'approved_{p_id}') == 'on'
                complete = request.POST.get(f'complete_{p_id}') == 'on'

                plan_row.modified_year = int(mod_yr) if mod_yr else None
                plan_row.project_number = proj_num if proj_num else None
                plan_row.is_approved = approved
                plan_row.is_complete = complete
                
                if approved and complete:
                    plan_row.save()
                    eq = plan_row.equipment
                    next_cycle = plan_row.iteration_cycle + 1
                    
                    overhaul_period = eq.Overhaul_Period if eq.Overhaul_Period else 12000
                    next_hours_target = overhaul_period * next_cycle
                    
                    found_next_year = current_year + 1
                    for yr in range(current_year + 1, current_year + 15):
                        res = calculate_next_intervention(eq, yr, current_year)
                        if res:
                            found_next_year = yr
                            break
                            
                    next_res = calculate_next_intervention(eq, found_next_year, current_year)
                    next_type = next_res['type'] if next_res else 'Rebuild'
                    next_cost = next_res['cost'] if next_res else Decimal('0.00')
                    
                    RebuildPlanRow.objects.get_or_create(
                        equipment=eq,
                        calculated_year=found_next_year,
                        intervention_type=next_type,
                        iteration_cycle=next_cycle,
                        defaults={'intervention_cost': next_cost}
                    )
                else:
                    plan_row.save()
            return redirect('reliability:rebuild_plan')

    eq_query = Equipment.objects.select_related('Asset_Type', 'Equipment_Type').filter(Equipment_Status='In Service')
    if asset_type_val:
        eq_query = eq_query.filter(Asset_Type__name__icontains=asset_type_val)
    if eq_type_val:
        eq_query = eq_query.filter(Equipment_Type__Equipment_Type__icontains=eq_type_val)
    if eq_num_val:
        eq_query = eq_query.filter(Equipment_Number__icontains=eq_num_val)

    eq_query = eq_query.order_by('Equipment_Number')

    active_plan_rows = []
    yearly_budget_totals = {yr: Decimal('0.00') for yr in five_year_timeline}
    scatter_data_points = []
    
    unique_eq_types = sorted(list(set(eq.Equipment_Type.Equipment_Type if eq.Equipment_Type else "Unassigned" for eq in eq_query)))

    for eq in eq_query:
        if not eq.Overhaul_Period or not eq.End_of_Life:
            eq.current_meter_value_display = "Not Configured"
            continue
            
        active_plan = RebuildPlanRow.objects.filter(equipment=eq, is_complete=False).order_by('iteration_cycle').first()
        
        priority_risk_index = get_combined_priority_score(eq, kpi_score_weight=0.5, cond_mon_weight=0.5)
        
        eq.priority_risk_score = priority_risk_index
        
        active_plan.priority_risk_score = priority_risk_index
        active_plan_rows.append(active_plan)

        imminent_plan_found = False

        for forecast_year in five_year_timeline:
            intervention = calculate_next_intervention(eq, forecast_year, current_year)
            
            if intervention:
                cost_dec = Decimal(str(intervention['cost']))
                yearly_budget_totals[forecast_year] += cost_dec
                
                eq_type_label = eq.Equipment_Type.Equipment_Type if eq.Equipment_Type else "Unassigned"
                if eq_type_label in unique_eq_types:
                    y_index = unique_eq_types.index(eq_type_label)
                    scatter_data_points.append({
                        'x': int(forecast_year),
                        'y': int(y_index),
                        'cost': float(cost_dec),
                        'display_text': intervention['label'],
                        'machine_label': f"{eq.Equipment_Number} ({intervention['type']})"
                    })
                
                if not imminent_plan_found:
                    if not active_plan:
                        active_plan = RebuildPlanRow(
                            equipment=eq,
                            calculated_year=forecast_year,
                            intervention_type=intervention['type'],
                            intervention_cost=cost_dec
                        )
                    else:
                        active_plan.calculated_year = forecast_year
                        active_plan.intervention_type = intervention['type']
                        active_plan.intervention_cost = cost_dec
                        
                    imminent_plan_found = True

        if not active_plan:
            active_plan = RebuildPlanRow(
                equipment=eq,
                calculated_year=current_year + 5,
                intervention_type='Rebuild',
                intervention_cost=Decimal('0.00')
            )
            calculate_next_intervention(eq, current_year, current_year)

        active_plan.equipment.current_meter_value_display = eq.current_meter_value_display
        active_plan.priority_risk_score = priority_risk_index
        active_plan_rows.append(active_plan)

    if sort_by == 'priority_score':
        active_plan_rows.sort(key=lambda x: x.priority_risk_score, reverse=True)
    elif sort_by == '-priority_score':
        active_plan_rows.sort(key=lambda x: x.priority_risk_score)
    elif sort_by == '-equipment_number':
        active_plan_rows.sort(key=lambda x: x.equipment.Equipment_Number, reverse=True)
    else:
        active_plan_rows.sort(key=lambda x: x.equipment.Equipment_Number)

    formatted_datasets = [{'label': 'Capital Planned Interventions', 'data': scatter_data_points, 'pointRadius': 0, 'hoverRadius': 8}]
    summary_table_data = [{'year': yr, 'total': yearly_budget_totals[yr]} for yr in five_year_timeline]
        
    all_suggestions = Equipment.objects.filter(Equipment_Status='In Service')
    if eq_type_val:
        all_suggestions = all_suggestions.filter(Equipment_Type__Equipment_Type__icontains=eq_type_val)
    elif asset_type_val:
        all_suggestions = all_suggestions.filter(Asset_Type__name__icontains=asset_type_val)

    return render(request, 'reliability/five_year_plan.html', {
        'plan_rows': active_plan_rows,
        'timeline': five_year_timeline,
        'summary_table': summary_table_data,
        'asset_types': AssetType.objects.all(),
        'eq_type_choices': EQ_Type.objects.all(),
        'all_equipment_suggestions': all_suggestions.order_by('Equipment_Number'),
        'asset_type_val': asset_type_val,
        'eq_type_val': eq_type_val,
        'eq_num_val': eq_num_val,
        'sort': sort_by,
        'timeline_json': json.dumps(five_year_timeline),
        'y_axis_categories_json': json.dumps(unique_eq_types),
        'datasets_json': json.dumps(formatted_datasets),
    })

def filter_eq_types(request):
    """Returns option blocks matching the selected Asset Type text name."""
    asset_type_name = request.GET.get('asset_type', '').strip()
    
    if asset_type_name:
        eq_types = EQ_Type.objects.filter(Asset_Type__name__icontains=asset_type_name)
    else:
        eq_types = EQ_Type.objects.all()
        
    html = '<option value="">All EQ Types...</option>'
    for eqt in eq_types:
        html += f'<option value="{eqt.Equipment_Type}">{eqt.Equipment_Type}</option>'
        
    return HttpResponse(html)

def filter_eq_numbers(request):
    """Returns option blocks matching the selected EQ Type text description."""
    eq_type_name = request.GET.get('eq_type', '').strip()
    
    if eq_type_name:
        equipment = Equipment.objects.filter(
            Equipment_Type__Equipment_Type__icontains=eq_type_name,
            Equipment_Status='In Service'
        ).order_by('Equipment_Number')
    else:
        equipment = Equipment.objects.filter(Equipment_Status='In Service').order_by('Equipment_Number')
        
    html = '<option value="">Search ID...</option>'
    for eq in equipment:
        display_label = f"{eq.Equipment_Number} - {eq.Equipment_Description}"
        html += f'<option value="{eq.Equipment_Number}">{display_label}</option>'
        
    return HttpResponse(html)

