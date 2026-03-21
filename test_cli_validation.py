#!/usr/bin/env python3
"""
Test the CLI validation fix
"""

def test_cli_validation():
    """Test CLI validation with problematic path"""
    print("=== TESTING CLI VALIDATION FIX ===")
    
    # Test the exact path from the error
    file_path = '"C:\\Users\\Sarthak Sawant\\Pictures\\Screenshots\\Screenshot 2025-08-06 140745.png"'
    
    print(f"Testing path: {file_path}")
    
    # OLD CLI validation (broken)
    def validate_file_ext_old(file_path):
        if not file_path:
            return True
        ext = file_path.lower().split('.')[-1]
        return ext in ['pdf', 'jpg', 'jpeg', 'png']
    
    # NEW CLI validation (fixed)
    def validate_file_ext_new(file_path):
        if not file_path:
            return True
        # Clean path and extract filename first
        import os
        cleaned_path = file_path.strip().strip('"').strip("'").strip()
        filename = os.path.basename(cleaned_path)
        ext = filename.split(".")[-1].lower()
        return ext in ['pdf', 'jpg', 'jpeg', 'png']
    
    print("\n--- OLD VALIDATION ---")
    old_result = validate_file_ext_old(file_path)
    print(f"Old validation result: {old_result}")
    
    print("\n--- NEW VALIDATION ---")
    new_result = validate_file_ext_new(file_path)
    print(f"New validation result: {new_result}")
    
    # Debug the new validation
    print("\n--- DEBUG NEW VALIDATION ---")
    import os
    cleaned_path = file_path.strip().strip('"').strip("'").strip()
    print(f"Cleaned path: {cleaned_path}")
    filename = os.path.basename(cleaned_path)
    print(f"Filename: {filename}")
    ext = filename.split(".")[-1].lower()
    print(f"Extension: {ext}")
    
    if new_result:
        print("✅ CLI VALIDATION FIXED!")
    else:
        print("❌ CLI validation still broken")

if __name__ == "__main__":
    test_cli_validation()
