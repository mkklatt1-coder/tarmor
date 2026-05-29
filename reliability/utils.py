from decimal import Decimal
from datetime import date, datetime, timedelta
from equipment.models import Component, ComponentHistory
from meters.models import MeterReading
from condition_monitoring.models import MagPlug, FilterRating, ValveSet, ValveSetReading, CycleTime, CycleTimeMeasurement, CylinderTemp, CylinderTempReading, ShortTermCM
from equipment.models import Component, ComponentHistory, MachineShiftStatus, Equipment
from django.db.models import Avg, Sum
from work_orders.models import WorkOrder
from timesheets.models import Timesheet
from purchasing.models import Purchase
from .models import RebuildPlanRow

def calculate_machine_cph_data(equipment_obj, start_dt, end_dt):
    work_orders = WorkOrder.objects.filter(
        equipment=equipment_obj,
        date_closed__range=[start_dt, end_dt]
    )
    
    if not work_orders.exists():
        return 0.0

    readings = MeterReading.objects.filter(
        Equipment=equipment_obj, 
        Date__range=[start_dt.date(), end_dt.date()]
    ).order_by('Date')

    meter_delta = 0.0
    if readings.count() >= 2:
        meter_delta = float((readings.last().Total_Meter_Value or 0) - (readings.first().Total_Meter_Value or 0))

    if meter_delta <= 0:
        return 0.0

    shop_rate = equipment_obj.Garage.Shop_Rate if equipment_obj.Garage else Decimal('0.00')
    ts_hours = Timesheet.objects.filter(work_order__in=work_orders).aggregate(Sum('total_time'))['total_time__sum'] or 0
    labour_cost = float(shop_rate) * float(ts_hours)
    
    parts_cost = float(Purchase.objects.filter(wo_cc__in=work_orders).aggregate(Sum('grand_total'))['grand_total__sum'] or 0)
    total_cost = labour_cost + parts_cost
    
    return total_cost / meter_delta

def calculate_machine_mttr_data(equipment_obj, start_dt, end_dt):
    work_orders = WorkOrder.objects.filter(
        equipment=equipment_obj,
        work_type__work_type__in=["CF", "CP", "WTY"],
        date_created__range=[start_dt, end_dt],
        date_closed__isnull=False
    )

    total_repair_hours = 0.0
    completed_repairs_count = 0

    for wo in work_orders:
        if wo.machine_oos == 'Yes':
            duration = wo.date_closed - wo.date_created
            repair_time = duration.total_seconds() / 3600.0
        else:
            repair_time = float(Timesheet.objects.filter(work_order=wo).aggregate(
                total=Sum('total_time'))['total'] or 0.0)
        
        total_repair_hours += repair_time
        completed_repairs_count += 1

    return total_repair_hours / completed_repairs_count if completed_repairs_count > 0 else 0.0

def calculate_asset_reliability_score(eq):
    scores_sum = 0.0
    metrics_count = 0
    latest_reading = MeterReading.objects.filter(Equipment_id=eq.id).order_by('-Date', '-id').first()
    current_machine_hours = float(latest_reading.Total_Meter_Value) if latest_reading and latest_reading.Total_Meter_Value is not None else 0.0
    today_date = date.today()
    one_year_ago = today_date - timedelta(days=365)
    s_dt = datetime.combine(one_year_ago, datetime.min.time())
    e_dt = datetime.combine(today_date, datetime.max.time())

    # ==========================================
    # PART 1: POWERTRAIN COMPONENTS LIFECYCLE SCORING
    # ==========================================
    base_components = Component.objects.filter(Equipment=eq, Status='Installed')

    for comp in base_components:
        expected_life = float(comp.Expected_Lifespan) if comp.Expected_Lifespan and comp.Expected_Lifespan > 0 else 12000.0
        installation_hours = 0

        latest_change = ComponentHistory.objects.filter(
            Equipment=eq,
            Component=comp
        ).order_by('-Change_Date', '-id').first()
            
        if latest_change and latest_change.Meter_Reading is not None:
            installation_hours = float(latest_change.Meter_Reading)
        else:
            installation_hours = 0.0

        component_run_hours = max(0.0, current_machine_hours - installation_hours)
        comp_score = component_run_hours / expected_life

        scores_sum += comp_score
        metrics_count += 1

    # ==========================================
    # PART 2: KPI OPERATIONAL EFFICIENCY SCORING
    # ==========================================
    
    # A&U Score
    today = date.today()
    one_year_ago = today - timedelta(days=365)

    shift_logs = MachineShiftStatus.objects.filter(
        equipment=eq,
        report__date__range=[one_year_ago, today]
    )

    availability_avg = 0.85
    utilisation_avg = 0.65

    if shift_logs.exists():
        averages = shift_logs.aggregate(
            avg_available=Avg('available'), 
            avg_down=Avg('total_down')
        )
        
        if averages['avg_available'] is not None:
            availability_avg = min(1.0, max(0.0, float(averages['avg_available']) / 12.0))
            
        if averages['avg_down'] is not None:
            utilisation_avg = min(1.0, max(0.0, float(averages['avg_down']) / 12.0))

    availability_score = 1.0 - availability_avg
    scores_sum += availability_score
    metrics_count += 1

    utilisation_score = utilisation_avg * 0.01 
    scores_sum += utilisation_score
    metrics_count += 1
    
    # Cost per Hour
    individual_cph = calculate_machine_cph_data(eq, s_dt, e_dt)
    peer_fleet_machines = Equipment.objects.filter(Equipment_Type=eq.Equipment_Type, Equipment_Status='In Service')
    
    fleet_cph_sum = 0.0
    fleet_valid_count = 0

    for peer in peer_fleet_machines:
        peer_cph = calculate_machine_cph_data(peer, s_dt, e_dt)
        if peer_cph > 0:
            fleet_cph_sum += peer_cph
            fleet_valid_count += 1

    fleet_avg_cph = fleet_cph_sum / fleet_valid_count if fleet_valid_count > 0 else 0.0

    if individual_cph > 0 and fleet_avg_cph > 0:
        cost_score = individual_cph / fleet_avg_cph
    else:
        cost_score = 1.0
        
    scores_sum += cost_score
    metrics_count += 1

    # Failure Frequency
    failures_count = WorkOrder.objects.filter(
        equipment=eq,
        work_type__work_type__in=["CF", "CP", "WTY"],
        date_created__range=[s_dt, e_dt]
    ).count()

    past_year_readings = MeterReading.objects.filter(
        Equipment=eq, 
        Date__range=[one_year_ago, today_date]
    ).order_by('Date')
    
    accumulated_hours = 0.0
    if past_year_readings.exists():
        first_val = past_year_readings.first().Total_Meter_Value or 0
        last_val = past_year_readings.last().Total_Meter_Value or 0
        accumulated_hours = float(max(last_val - first_val, 0))

    failure_frequency_score = (failures_count / accumulated_hours) if accumulated_hours > 0 else 0.0
    
    scores_sum += failure_frequency_score
    metrics_count += 1

    # MTTR
    failures_count = WorkOrder.objects.filter(
        equipment=eq,
        work_type__work_type__in=["CF", "CP", "WTY"],
        date_created__range=[s_dt, e_dt]
    ).count()

    past_year_readings = MeterReading.objects.filter(
        Equipment=eq, 
        Date__range=[one_year_ago, today_date]
    ).order_by('Date')
    
    accumulated_hours = 0.0
    if past_year_readings.exists():
        first_val = past_year_readings.first().Total_Meter_Value or 0
        last_val = past_year_readings.last().Total_Meter_Value or 0
        accumulated_hours = float(max(last_val - first_val, 0))

    failure_frequency_score = (failures_count / accumulated_hours) if accumulated_hours > 0 else 0.0
    scores_sum += failure_frequency_score
    metrics_count += 1

    # MTTR
    individual_mttr = calculate_machine_mttr_data(eq, s_dt, e_dt)
    fleet_mttr_sum = 0.0
    fleet_mttr_count = 0
    for peer in peer_fleet_machines:
        peer_mttr = calculate_machine_mttr_data(peer, s_dt, e_dt)
        if peer_mttr > 0:
            fleet_mttr_sum += peer_mttr
            fleet_mttr_count += 1
            
    fleet_avg_mttr = fleet_mttr_sum / fleet_mttr_count if fleet_mttr_count > 0 else 0.0
    if individual_mttr > 0 and fleet_avg_mttr > 0:
        mttr_score = individual_mttr / fleet_avg_mttr
    else:
        mttr_score = 1.0
        
    scores_sum += mttr_score
    metrics_count += 1

    if metrics_count > 0:
        return scores_sum / metrics_count
    return 0.0

def calculate_condition_monitoring_score(eq):
    total_score = 0.0
    total_baseline = 0.0
    metrics_evaluated = 0

    last_completed_intervention = RebuildPlanRow.objects.filter(
        equipment=eq, 
        is_complete=True
    ).order_by('-calculated_year').first()
    
    if last_completed_intervention:
        window_start_date = date(last_completed_intervention.calculated_year, 1, 1)
    else:
        window_start_date = eq.Commissioning_Date if eq.Commissioning_Date else date(2000, 1, 1)

    # 1. MAG PLUGS (Baseline = Start Value)
    mag_compartments = MagPlug.objects.filter(
        equipment_id=eq.id, 
        date__gte=window_start_date
    ).values_list('compartment', flat=True).distinct()

    for comp_name in mag_compartments:
        if not comp_name:
            continue
        
        comp_readings = MagPlug.objects.filter(
            equipment_id=eq.id,
            compartment=comp_name,
            date__gte=window_start_date
        ).order_by('date')
        
        if comp_readings.count() >= 2:
            start_val = float(comp_readings.first().plug_rating or 0.0)
            end_val = float(comp_readings.last().plug_rating or 0.0)
            
            total_score += (end_val - start_val)
            total_baseline += start_val if start_val > 0 else 1.0
            metrics_evaluated += 1

    # 2. FILTERS
    filter_compartments = FilterRating.objects.filter(
        equipment_id=eq.id, 
        date__gte=window_start_date
    ).values_list('compartment', flat=True).distinct()

    for comp_name in filter_compartments:
        if not comp_name:
            continue
        comp_readings = FilterRating.objects.filter(
            equipment_id=eq.id,
            compartment=comp_name,
            date__gte=window_start_date
        ).order_by('date')
        
        if comp_readings.count() >= 2:
            start_val = float(comp_readings.first().filter_rating or 0.0)
            end_val = float(comp_readings.last().filter_rating or 0.0)
            
            total_score += (end_val - start_val)
            total_baseline += start_val if start_val > 0 else 1.0
            metrics_evaluated += 1

    # 3. CYCLE TIMES
    window_measurements = CycleTimeMeasurement.objects.filter(
        cycle_time__equipment_id=eq.id,
        cycle_time__date__gte=window_start_date
    )

    unique_combinations = window_measurements.values('system', 'position').distinct()
    for combo in unique_combinations:
        sys_name = combo['system']
        pos_name = combo['position']
        if not sys_name or not pos_name:
            continue
        combo_readings = CycleTimeMeasurement.objects.filter(
            cycle_time__equipment_id=eq.id,
            cycle_time__date__gte=window_start_date,
            system=sys_name,
            position=pos_name
        ).order_by('cycle_time__date', 'cycle_time__id')

        if combo_readings.count() >= 2:
            start_time = float(combo_readings.first().time or 0.0)
            end_time = float(combo_readings.last().time or 0.0)
            
            total_score += (end_time - start_time)
            total_baseline += start_time if start_time > 0 else 1.0
            metrics_evaluated += 1

    # 4. VALVE TRENDS
    window_valves = ValveSetReading.objects.filter(
        valve_set__equipment_id=eq.id,
        valve_set__date__gte=window_start_date
    )
    unique_valves = window_valves.values('cylinder_number', 'int_exh', 'valve_number').distinct()

    for v_combo in unique_valves:
        cyl = v_combo['cylinder_number']
        typ = v_combo['int_exh']
        num = v_combo['valve_number']
        if not cyl or not typ or not num: continue

        valve_history = ValveSetReading.objects.filter(
            valve_set__equipment_id=eq.id,
            valve_set__date__gte=window_start_date,
            cylinder_number=cyl,
            int_exh=typ,
            valve_number=num
        ).order_by('valve_set__date', 'valve_set__id')

        valve_count = valve_history.count()
        if valve_count >= 2:
            cumulative_valve_wear = 0.0
            history_list = list(valve_history)

            base_reference_lash = float(history_list[0].valve_setting or 0.025)
            for i in range(1, valve_count):
                previous_reading = history_list[i-1]
                current_reading = history_list[i]
                
                prev_setting = float(previous_reading.valve_setting or 0.0)
                curr_setting = float(current_reading.valve_setting or 0.0)

                if prev_setting > base_reference_lash + 0.002 or prev_setting < base_reference_lash - 0.002:
                    step_wear = abs(curr_setting - base_reference_lash)
                else:
                    step_wear = abs(curr_setting - prev_setting)
                
                cumulative_valve_wear += step_wear
                if step_wear > 0.002:
                    total_score += 1.0

            total_score += cumulative_valve_wear
            total_baseline += base_reference_lash if base_reference_lash > 0 else 0.025
            metrics_evaluated += 1

    window_temps = CylinderTempReading.objects.filter(
        cylinder_temp__equipment_id=eq.id,
        cylinder_temp__date__gte=window_start_date
    )
    unique_temp_locations = window_temps.values_list('cylinder_number', flat=True).distinct()

    def parse_to_celsius(reading_obj):
        try:
            raw_val = float(reading_obj.temp_reading or 0.0)
            if reading_obj.uom == 'degrees F':
                return (raw_val - 32.0) * (5.0 / 9.0)
            return raw_val
        except (ValueError, TypeError):
            return 0.0

    for location_id in unique_temp_locations:
        if not location_id: continue
            
        loc_readings = CylinderTempReading.objects.filter(
            cylinder_temp__equipment_id=eq.id,
            cylinder_number=location_id,
            cylinder_temp__date__gte=window_start_date
        ).order_by('cylinder_temp__date', 'cylinder_temp__id')

        if loc_readings.count() >= 2:
            first_reading = loc_readings.first()
            last_reading = loc_readings.last()

            first_parent_id = first_reading.cylinder_temp_id
            first_group = CylinderTempReading.objects.filter(cylinder_temp_id=first_parent_id)
            
            first_group_temps = [parse_to_celsius(r) for r in first_group if parse_to_celsius(r) > 0]
            first_group_avg = sum(first_group_temps) / len(first_group_temps) if first_group_temps else 0.0
            
            start_temp = parse_to_celsius(first_reading)
            start_deviation = (abs(start_temp - first_group_avg) / first_group_avg) if first_group_avg > 0 else 0.0

            last_parent_id = last_reading.cylinder_temp_id
            last_group = CylinderTempReading.objects.filter(cylinder_temp_id=last_parent_id)
            last_group_temps = [parse_to_celsius(r) for r in last_group if parse_to_celsius(r) > 0]
            last_group_avg = sum(last_group_temps) / len(last_group_temps) if last_group_temps else 0.0
            
            end_temp = parse_to_celsius(last_reading)
            end_deviation = (abs(end_temp - last_group_avg) / last_group_avg) if last_group_avg > 0 else 0.0
            deviation_trend_delta = end_deviation - start_deviation
            
            total_score += deviation_trend_delta
            total_baseline += 1.0
            metrics_evaluated += 1

    # 6. SHORT TERM ACTIONS
    individual_st_count = ShortTermCM.objects.filter(equipment_id=eq.id, complete__iexact='No').count()
    
    peer_fleet = Equipment.objects.filter(Equipment_Type=eq.Equipment_Type, Equipment_Status='In Service')
    
    peer_st_sum = 0
    peer_valid_count = 0
    
    for peer in peer_fleet:
        peer_count = ShortTermCM.objects.filter(equipment_id=peer.id, complete__iexact='No').count()
        peer_st_sum += peer_count
        peer_valid_count += 1
        
    fleet_avg_st = float(peer_st_sum) / float(peer_valid_count) if peer_valid_count > 0 else 0.0

    if individual_st_count > 0 and fleet_avg_st > 0:
        total_score += (float(individual_st_count) / fleet_avg_st)
        total_baseline += 1.0
        metrics_evaluated += 1
    elif individual_st_count > 0:
        total_score += float(individual_st_count)
        total_baseline += 1.0
        metrics_evaluated += 1

    if metrics_evaluated > 0 and total_baseline > 0:
        return total_score / total_baseline
    return 0.0

def get_combined_priority_score(eq, kpi_score_weight=0.5, cond_mon_weight=0.5):
    """
    Merges Part 1 (Component Health & KPIs) with Part 2 (Condition Monitoring)
    using customizable weighting constraints.
    """
    kpi_index = calculate_asset_reliability_score(eq)
    cond_mon_index = calculate_condition_monitoring_score(eq)
    
    master_priority_rank = (kpi_index * kpi_score_weight) + (cond_mon_index * cond_mon_weight)
    return round(master_priority_rank, 4)