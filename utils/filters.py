# utils/filters.py
from datetime import datetime, date
from flask import request

def get_month_options():
    """Generate month options for dropdown"""
    months = [
        ('01', 'January'),
        ('02', 'February'), 
        ('03', 'March'),
        ('04', 'April'),
        ('05', 'May'),
        ('06', 'June'),
        ('07', 'July'),
        ('08', 'August'),
        ('09', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ]
    
    current_year = datetime.now().year
    current_month = datetime.now().strftime('%m')
    
    options = []
    # Add current year months
    for month_num, month_name in months:
        value = f"{month_num}-{current_year}"
        label = f"{month_name} {current_year}"
        selected = (month_num == current_month)
        options.append((value, label, selected))
    
    # Add previous year months
    for year in [current_year - 1, current_year - 2]:
        for month_num, month_name in months:
            value = f"{month_num}-{year}"
            label = f"{month_name} {year}"
            selected = False
            options.append((value, label, selected))
    
    return options

def get_period_from_request():
    """Get period from request with fallback to current month"""
    period = request.args.get('period', '')
    if not period:
        period = datetime.now().strftime('%m-%Y')
    return period

def parse_period(period):
    """Parse period string to start and end dates"""
    try:
        month, year = period.split('-')
        start_date = date(int(year), int(month), 1)
        
        # Calculate end date
        if int(month) == 12:
            end_date = date(int(year) + 1, 1, 1)
        else:
            end_date = date(int(year), int(month) + 1, 1)
        
        from datetime import timedelta
        end_date = end_date - timedelta(days=1)
        
        return start_date, end_date
    except:
        # Fallback to current month
        today = date.today()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1)
        else:
            end_date = date(today.year, today.month + 1, 1)
        end_date = end_date - timedelta(days=1)
        return start_date, end_date
