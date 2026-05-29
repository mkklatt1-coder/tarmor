from django.db import migrations
def load_effval_rules(apps, schema_editor):
    EffValRule = apps.get_model("moc", "EffValRule")
    EffValPointRange = apps.get_model("moc", "EffValPointRange")
    rules = [
        # ---------------- Effort rules ----------------
        {
            "name": "safety",
            "label": "Safety (months)",
            "category": "EFFORT",
            "source": "risk_total_value",
            "weight": 0.20,
            "ranges": [
                ("0", 0),
                ("1-50", 0),
                ("51-100", 2),
                ("101-200", 4),
                ("201-300", 6),
                ("301-400", 8),
                (">400", 10),
            ]
        },
        {
            "name": "setup",
            "label": "Setup & Test",
            "category": "EFFORT",
            "source": "setup_months",
            "weight": 0.10,
            "ranges": [
                ("0-6", 2),
                ("7-12", 4),
                ("13-18", 6),
                ("19-24", 8),
                (">24", 10),
            ]
        },
        {
            "name": "implementation",
            "label": "Implementation (months)",
            "category": "EFFORT",
            "source": "implementation_months",
            "weight": 0.15,
            "ranges": [
                ("0-3", 2),
                ("4-6", 4),
                ("7-9", 6),
                ("10-12", 8),
                (">12", 10),
            ]
        },
        {
            "name": "downtime",
            "label": "Downtime (weeks)",
            "category": "EFFORT",
            "source": "eq_downtime",
            "weight": 0.10,
            "ranges": [
                ("0-6", 2),
                ("7-12", 4),
                ("13-18", 6),
                ("19-24", 8),
                (">24", 10),
            ]
        },
        {
            "name": "project_cost",
            "label": "Capital Cost",
            "category": "EFFORT",
            "source": "project_cost",
            "weight": 0.15,
            "ranges": [
                ("0", 2),
                ("1-5000", 4),
                ("5001-10000", 6),
                ("10001-50000", 8),
                (">50000", 10),
            ]
        },
        {
            "name": "inventory",
            "label": "Inventory Cost",
            "category": "EFFORT",
            "source": "inventory_cost",
            "weight": 0.05,
            "ranges": [
                ("0", 2),
                ("1-5000", 4),
                ("5001-10000", 6),
                ("10001-50000", 8),
                (">50000", 10),
            ]
        },
        {
            "name": "contractor",
            "label": "Contractor Hours",
            "category": "EFFORT",
            "source": "contractor_hours",
            "weight": 0.15,
            "ranges": [
                ("0-50", 3),
                ("51-100", 4),
                ("101-200", 6),
                ("201-300", 8),
                (">300", 10),
            ]
        },
        {
            "name": "warranty",
            "label": "Warranty Impact",
            "category": "EFFORT",
            "source": "warranty_impact",
            "weight": 0.10,
            "ranges": [
                ("None", 0),
                ("Low", 3),
                ("Med", 6),
                ("High", 10),
            ]
        },
        # ---------------- Value rules ----------------
        {
            "name": "savings_confirmed",
            "label": "Savings (hard)",
            "category": "VALUE",
            "source": "savings_confirmed",
            "weight": 0.30,
            "ranges": [
                ("0-10000", 2),
                ("10001-50000", 4),
                ("50001-75000", 6),
                ("75001-100000", 8),
                (">100000", 10),
            ]
        },
        {
            "name": "savings_soft",
            "label": "Savings (soft)",
            "category": "VALUE",
            "source": "savings_soft",
            "weight": 0.15,
            "ranges": [
                ("0-10000", 2),
                ("10001-50000", 4),
                ("50001-75000", 6),
                ("75001-100000", 8),
                (">100000", 10),
            ]
        },
        {
            "name": "production_gain",
            "label": "Production Gains (%)",
            "category": "VALUE",
            "source": "production_gain",
            "weight": 0.30,
            "ranges": [
                ("0-5", 2),
                ("6-10", 4),
                ("11-15", 6),
                ("16-20", 8),
                (">20", 10),
            ]
        },
        {
            "name": "social_impact",
            "label": "Social Impact",
            "category": "VALUE",
            "source": "social_impact",
            "weight": 0.10,
            "ranges": [
                ("None", 0),
                ("Low", 3),
                ("Med", 6),
                ("High", 10),
            ]
        },
        {
            "name": "safety_gain",
            "label": "Environmental / Safety Gains",
            "category": "VALUE",
            "source": "safety_gain",
            "weight": 0.15,
            "ranges": [
                ("None", 0),
                ("Low", 3),
                ("Med", 6),
                ("High", 10),
            ]
        },
    ]
    for r in rules:
        rule = EffValRule.objects.create(
            name=r["name"],
            label=r["label"],
            category=r["category"],
            source_field=r["source"],
            weight=r["weight"]
        )
        for value_key, points in r["ranges"]:
            EffValPointRange.objects.create(
                rule=rule,
                value_key=value_key,
                points=points
            )
def unload_effval_rules(apps, schema_editor):
    EffValRule = apps.get_model("moc", "EffValRule")
    EffValPointRange = apps.get_model("moc", "EffValPointRange")
    EffValPointRange.objects.all().delete()
    EffValRule.objects.all().delete()
class Migration(migrations.Migration):
    dependencies = [
        ("moc", "0001_initial"),  # <-- update to match your real migration number
    ]
    operations = [
        migrations.RunPython(load_effval_rules, unload_effval_rules),
    ]