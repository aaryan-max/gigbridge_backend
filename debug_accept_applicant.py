#!/usr/bin/env python3
"""
Debug script for Accept Applicant functionality
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def debug_accept_applicant():
    print("🔍 Debugging Accept Applicant functionality...")
    print("=" * 60)
    
    try:
        # Step 1: Check if client 1 exists
        print("\n1️⃣ Checking client 1...")
        client_res = requests.get(f"{BASE_URL}/client/profile/1")
        print(f"Status: {client_res.status_code}")
        if client_res.status_code == 200:
            print("✅ Client 1 exists")
        else:
            print("❌ Client 1 not found")
            return False
            
        # Step 2: Get client projects
        print("\n2️⃣ Getting client projects...")
        proj_res = requests.get(f"{BASE_URL}/client/projects", params={"client_id": 1})
        print(f"Status: {proj_res.status_code}")
        if proj_res.status_code not in [200, 201]:
            print("❌ Failed to get projects")
            return False
            
        proj_data = proj_res.json()
        projects = proj_data.get("projects") or []
        print(f"Found {len(projects)} projects")
        
        if not projects:
            print("❌ No projects found for client 1")
            return False
            
        # Step 3: Find a project with applicants
        print("\n3️⃣ Looking for project with applicants...")
        project_with_applicants = None
        for p in projects:
            pid = p.get("project_id")
            print(f"  Checking project {pid}...")
            
            # Get applicants for this project
            app_res = requests.get(f"{BASE_URL}/client/projects/applicants", params={
                "client_id": 1,
                "project_id": pid
            })
            print(f"    Applicants API Status: {app_res.status_code}")
            
            if app_res.status_code in [200, 201]:
                app_data = app_res.json() or {}
                applicants = app_data.get("applicants") or []
                print(f"    Found {len(applicants)} applicants")
                
                # Look for APPLIED status
                applied_applicants = [a for a in applicants if a.get("status") == "APPLIED"]
                print(f"    APPLIED applicants: {len(applied_applicants)}")
                
                if applied_applicants:
                    project_with_applicants = {
                        "project": p,
                        "applicants": applied_applicants
                    }
                    print(f"    ✅ Found project {pid} with {len(applied_applicants)} applied applicants")
                    break
            else:
                print(f"    ❌ Failed to get applicants: {app_res.text}")
                
        if not project_with_applicants:
            print("❌ No project with APPLIED applicants found")
            return False
            
        # Step 4: Try to accept an applicant
        print("\n4️⃣ Attempting to accept applicant...")
        project = project_with_applicants["project"]
        applicant = project_with_applicants["applicants"][0]  # Take first applied applicant
        
        project_id = project.get("project_id")
        application_id = applicant.get("application_id")
        
        print(f"  Project ID: {project_id}")
        print(f"  Application ID: {application_id}")
        print(f"  Applicant Status: {applicant.get('status')}")
        print(f"  Freelancer ID: {applicant.get('freelancer_id')}")
        
        # Call accept endpoint
        accept_res = requests.post(f"{BASE_URL}/client/projects/accept_application", json={
            "client_id": 1,
            "project_id": project_id,
            "application_id": application_id
        })
        
        print(f"  Accept API Status: {accept_res.status_code}")
        print(f"  Accept API Response: {accept_res.text}")
        
        if accept_res.status_code in [200, 201]:
            print("  ✅ Accept Applicant successful!")
            return True
        else:
            print("  ❌ Accept Applicant failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_accept_applicant()
    print("\n" + "=" * 60)
    if success:
        print("🎉 Accept Applicant functionality is working!")
    else:
        print("❌ Accept Applicant functionality needs fixing.")
