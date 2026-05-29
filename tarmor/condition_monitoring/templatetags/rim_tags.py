from django import template
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

register = template.Library()

@register.filter(name='get_due_color_class')
def get_due_color_class(next_test_date_str):
    """
    Evaluates a date string and returns a CSS class name based on status:
    Overdue = red, < 6 Months = amber, Clear = no class
    """
    if not next_test_date_str or str(next_test_date_str).lower() == 'scrap':
        return ''
        
    try:
        due_date = datetime.strptime(str(next_test_date_str), '%Y-%m-%d').date()
        today = date.today()
        
        if due_date < today:
            return 'status-overdue-red'
            
        coming_due_threshold = today + relativedelta(months=6)
        if due_date <= coming_due_threshold:
            return 'status-warning-amber'
            
    except (ValueError, TypeError):
        pass
        
    return ''