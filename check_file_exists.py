#!/usr/bin/env python3
"""
Check if the problematic file path exists
"""

import os

def check_file_exists():
    """Check if the file actually exists"""
    print("=== CHECKING FILE EXISTENCE ===")
    
    # Test the exact path from the error
    file_path = 'C:\\Users\\Sarthak Sawant\\Pictures\\Screenshots\\Screenshot 2025-08-06 140745.png'
    
    print(f"Checking: {file_path}")
    exists = os.path.exists(file_path)
    print(f"File exists: {exists}")
    
    if not exists:
        print("❌ FILE DOES NOT EXIST - This is the problem!")
        
        # Check if directory exists
        dir_path = 'C:\\Users\\Sarthak Sawant\\Pictures\\Screenshots'
        print(f"\nChecking directory: {dir_path}")
        dir_exists = os.path.exists(dir_path)
        print(f"Directory exists: {dir_exists}")
        
        if dir_exists:
            print("Files in directory:")
            try:
                files = os.listdir(dir_path)
                for f in files[:10]:  # Show first 10 files
                    if f.lower().endswith('.png'):
                        print(f"  - {f}")
            except Exception as e:
                print(f"Error listing files: {e}")
    else:
        print("✅ File exists - issue might be elsewhere")

if __name__ == "__main__":
    check_file_exists()
