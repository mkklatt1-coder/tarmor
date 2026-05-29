
def calculate_effval(moc):
    from moc.models import EffValRule, MOCEffValPoint
    cons = getattr(moc, "considerations", None)
    safety = getattr(moc, "safety", None)
    total_effort = 0
    total_value = 0
        
    for rule in EffValRule.objects.all():
        
        if hasattr(cons, rule.source_field):
            source_obj = cons
        elif safety and hasattr(safety, rule.source_field):
            source_obj = safety
        else:
            continue
        
        raw_key = getattr(source_obj, rule.source_field, None)
        if not raw_key:
            continue
        
        r = rule.ranges.filter(value_key=raw_key).first()
        if not r:
            continue
        points = r.points
        weighted_score = float(points) * float(rule.weight)
        
        if rule.category == EffValRule.EFFORT:
            total_effort += weighted_score
        else:
            total_value += weighted_score
    ratio = total_value / total_effort if total_effort else None

    effort_score = round(total_effort, 2)
    value_score = round(total_value, 2)
    ratio_score = round(total_value / total_effort, 3) if total_effort else None

    point_record, created = MOCEffValPoint.objects.update_or_create(
        moc=moc,
        defaults={
            "effort": effort_score,
            "value": value_score,
            "ratio": ratio_score
        }
    )

    return {
        "effort": effort_score,
        "value": value_score,
        "ratio": ratio_score,
        "instance": point_record
    }