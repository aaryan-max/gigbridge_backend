"""
Booking Service for GigBridge
Handles date/time slot validation and overlap checking for hire requests
"""

from datetime import datetime, date, time
from database import freelancer_db


def validate_date_format(date_str):
    """Validate date format YYYY-MM-DD"""
    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        return True, parsed_date
    except ValueError:
        return False, None


def validate_time_format(time_str):
    """Validate time format HH:MM"""
    try:
        parsed_time = datetime.strptime(time_str, "%H:%M").time()
        return True, parsed_time
    except ValueError:
        return False, None


def validate_date_time_slot(event_date_str, start_time_str, end_time_str):
    """
    Validate date and time slot according to business rules:
    1. Previous dates must not be accepted
    2. If selected date is today, start time must not be in the past
    3. End time must be greater than start time
    
    Returns:
        tuple: (is_valid, error_message, parsed_date, parsed_start_time, parsed_end_time)
    """
    # Validate date format
    is_valid_date, parsed_date = validate_date_format(event_date_str)
    if not is_valid_date:
        return False, "Invalid date format. Use YYYY-MM-DD", None, None, None
    
    # Validate time formats
    is_valid_start, parsed_start_time = validate_time_format(start_time_str)
    if not is_valid_start:
        return False, "Invalid start time format. Use HH:MM", None, None, None
    
    is_valid_end, parsed_end_time = validate_time_format(end_time_str)
    if not is_valid_end:
        return False, "Invalid end time format. Use HH:MM", None, None, None
    
    # Check if date is in the past
    today = date.today()
    if parsed_date < today:
        return False, "Past dates are not allowed", None, None, None
    
    # Check if time is in the past for today
    if parsed_date == today:
        now = datetime.now().time()
        if parsed_start_time < now:
            return False, "Start time cannot be in the past", None, None, None
    
    # Check if end time is after start time
    if parsed_end_time <= parsed_start_time:
        return False, "End time must be greater than start time", None, None, None
    
    return True, None, parsed_date, parsed_start_time, parsed_end_time


def check_time_overlap(freelancer_id, event_date_str, start_time_str, end_time_str):
    """
    Check if the freelancer has any existing hire requests that overlap with the selected time slot.
    
    Overlap logic:
    - Existing: 14:00 to 18:00, New: 16:00 to 19:00 -> overlap (reject)
    - Existing: 14:00 to 18:00, New: 18:00 to 20:00 -> no overlap (allow)
    
    Args:
        freelancer_id: ID of the freelancer
        event_date_str: Date in YYYY-MM-DD format
        start_time_str: Start time in HH:MM format
        end_time_str: End time in HH:MM format
    
    Returns:
        tuple: (has_overlap, overlapping_request)
    """
    try:
        conn = freelancer_db()
        cur = conn.cursor()
        
        # Get existing hire requests for the same freelancer and date
        # Consider requests that are PENDING, ACCEPTED, or ACTIVE (not rejected/completed)
        cur.execute("""
            SELECT id, job_title, start_time, end_time, status
            FROM hire_request
            WHERE freelancer_id = %s
            AND event_date = %s
            AND status IN ('PENDING', 'ACCEPTED', 'ACTIVE')
            ORDER BY start_time
        """, (freelancer_id, event_date_str))
        
        existing_requests = cur.fetchall()
        conn.close()
        
        if not existing_requests:
            return False, None
        
        # Parse new request times
        _, _, _, new_start_time, new_end_time = validate_date_time_slot(
            event_date_str, start_time_str, end_time_str
        )
        
        # Check for overlap with each existing request
        for req in existing_requests:
            req_id, job_title, existing_start_str, existing_end_str, status = req
            
            # Parse existing times
            _, _, _, existing_start_time, existing_end_time = validate_date_time_slot(
                event_date_str, existing_start_str, existing_end_str
            )
            
            # Check overlap: new_start < existing_end AND new_end > existing_start
            if (new_start_time < existing_end_time and new_end_time > existing_start_time):
                overlapping_request = {
                    'id': req_id,
                    'job_title': job_title,
                    'start_time': existing_start_str,
                    'end_time': existing_end_str,
                    'status': status
                }
                return True, overlapping_request
        
        return False, None
        
    except Exception as e:
        # If there's an error, be conservative and allow the booking
        # but log the error for debugging
        print(f"Error checking overlap: {e}")
        return False, None


def validate_hire_request_slot(freelancer_id, event_date_str, start_time_str, end_time_str):
    """
    Complete validation for hire request date/time slot
    
    Args:
        freelancer_id: ID of the freelancer
        event_date_str: Date in YYYY-MM-DD format
        start_time_str: Start time in HH:MM format  
        end_time_str: End time in HH:MM format
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # First validate the date/time format and basic rules
    is_valid, error_msg, parsed_date, parsed_start_time, parsed_end_time = validate_date_time_slot(
        event_date_str, start_time_str, end_time_str
    )
    
    if not is_valid:
        return False, error_msg
    
    # Then check for overlap with existing requests
    has_overlap, overlapping_req = check_time_overlap(
        freelancer_id, event_date_str, start_time_str, end_time_str
    )
    
    if has_overlap:
        overlap_info = f"Existing booking: {overlapping_req['job_title']} ({overlapping_req['start_time']}-{overlapping_req['end_time']})"
        return False, f"This freelancer is not available for the selected time slot. {overlap_info}"
    
    return True, None


def format_time_slot_display(event_date_str, start_time_str, end_time_str):
    """
    Format time slot for display in CLI and responses
    
    Returns:
        str: Formatted time slot display
    """
    return f"Date: {event_date_str}\nTime: {start_time_str} - {end_time_str}"
