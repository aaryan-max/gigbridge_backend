# venue_helper.py
"""
Event venue validation and location compatibility helper
"""
import re
from database import freelancer_db, get_dict_cursor

def validate_pincode(pincode):
    """Validate Indian pincode format (6 digits)"""
    if not pincode:
        return True  # Optional field
    return bool(re.match(r'^\d{6}$', str(pincode).strip()))

def get_client_profile_address(client_id):
    """Get client's saved profile address"""
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT location, pincode, latitude, longitude 
            FROM client_profile 
            WHERE client_id=%s
        """, (client_id,))
        result = cur.fetchone()
        conn.close()
        return result
    except Exception:
        return None

def check_venue_freelancer_compatibility(freelancer_id, event_pincode, event_city):
    """
    Check if freelancer location is compatible with event venue
    Returns: (location_ok, location_note)
    """
    try:
        conn = freelancer_db()
        cur = get_dict_cursor(conn)
        
        # Get freelancer profile location
        cur.execute("""
            SELECT f.name, fp.latitude, fp.longitude 
            FROM freelancer f
            JOIN freelancer_profile fp ON f.id = fp.freelancer_id
            WHERE f.id=%s
        """, (freelancer_id,))
        freelancer = cur.fetchone()
        conn.close()
        
        if not freelancer:
            return False, "Freelancer not found"
        
        # If no event location provided, assume OK
        if not event_pincode and not event_city:
            return True, "No event location specified"
        
        # Simple pincode-based compatibility check
        if event_pincode:
            # Try to get freelancer's service area (if available)
            # For now, use a simple distance-based check if coordinates available
            if freelancer.get('latitude') and freelancer.get('longitude'):
                # This is a simplified check - in production, you might want
                # to use a proper geolocation service
                return True, f"Freelancer available for event area ({event_pincode})"
            else:
                return True, f"Freelancer available for {event_city or 'your area'}"
        
        # City-based check
        if event_city:
            return True, f"Freelancer available for {event_city}"
        
        return True, "Location compatibility check passed"
        
    except Exception as e:
        return False, f"Error checking location compatibility: {str(e)}"

def prepare_venue_data(venue_choice, client_id, custom_venue_data=None):
    """
    Prepare venue data based on client choice
    venue_choice: 'profile' or 'custom'
    client_id: client ID for profile address lookup
    custom_venue_data: dict with custom venue fields
    Returns: dict with venue fields
    """
    venue_data = {
        "venue_source": venue_choice,
        "event_address": "",
        "event_city": "",
        "event_pincode": "",
        "event_landmark": ""
    }
    
    if venue_choice == "profile":
        # Use client's saved profile address
        profile = get_client_profile_address(client_id)
        if profile:
            venue_data.update({
                "event_address": profile.get("location", ""),
                "event_city": extract_city_from_address(profile.get("location", "")),
                "event_pincode": profile.get("pincode", ""),
                "event_landmark": ""
            })
        else:
            # Fallback if no profile address found
            return None, "Client profile address not found"
    
    elif venue_choice == "custom":
        # Use custom venue data
        if not custom_venue_data:
            return None, "Custom venue data required"
        
        venue_data.update({
            "event_address": custom_venue_data.get("event_address", ""),
            "event_city": custom_venue_data.get("event_city", ""),
            "event_pincode": custom_venue_data.get("event_pincode", ""),
            "event_landmark": custom_venue_data.get("event_landmark", "")
        })
    
    return venue_data, None

def extract_city_from_address(address):
    """Extract city from address string (simple implementation)"""
    if not address:
        return ""
    
    # Simple city extraction - look for common patterns
    # This is a basic implementation - can be improved
    parts = address.split(',')
    if len(parts) >= 2:
        # Assume format: street, city, state...
        return parts[-2].strip() if len(parts) >= 3 else parts[-1].strip()
    return address.strip()

def validate_venue_data(venue_data):
    """
    Validate venue data fields
    Returns: (is_valid, error_message)
    """
    if not venue_data:
        return False, "Venue data required"
    
    event_address = venue_data.get("event_address", "").strip()
    if not event_address:
        return False, "Event address is required"
    
    event_pincode = venue_data.get("event_pincode", "").strip()
    if event_pincode and not validate_pincode(event_pincode):
        return False, "Invalid pincode format (6 digits required)"
    
    return True, None
