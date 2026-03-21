import React, { useState, useEffect } from "react";
import DashboardHeader from "../components/DashboardHeader";
import DashboardSidebar from "../components/DashboardSidebar";
import ProfileCompletionCard from "../components/ProfileCompletionCard";
import ProfileHeader from "../components/ProfileHeader";
import ProfileDetails from "../components/ProfileDetails";
import CategoryDynamicSection from "../components/CategoryDynamicSection";
import PortfolioPreview from "../components/PortfolioPreview";
import EditProfileModal from "../components/EditProfileModal";
import "./dashboard.css";
import "./freelancerProfile.css";

const MOCK_PROFILE = {
  name: "John Smith",
  email: "john.smith@example.com",
  phone: "+1 (555) 123-4567",
  location: "San Francisco, CA",
  hourlyRate: 85,
  bio: "Passionate frontend developer with 5+ years of experience building modern web applications. Specialized in React, TypeScript, and creating beautiful user interfaces.",
  category: "Designer",
  skills: ["React", "TypeScript", "Node.js", "UI/UX Design", "Figma", "Tailwind CSS"],
  availability: true,
  profileImage: null,
  portfolio: [
    { id: 1, title: "E-commerce App", description: "A full-stack e-commerce solution", image: "https://images.unsplash.com/photo-1557821552-17105176677c?w=500" },
    { id: 2, title: "Portfolio Website", description: "Minimalist personal portfolio", image: "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?w=500" }
  ],
  experience: 5,
  completion: {
    basicInfo: true,
    skills: true,
    verification: false,
    portfolio: true
  }
};

export default function FreelancerProfilePage() {
  const [active, setActive] = useState("profile");
  const [profile, setProfile] = useState(MOCK_PROFILE);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  const handleUpdateProfile = (updatedData) => {
    setProfile(prev => ({ ...prev, ...updatedData }));
    setIsEditModalOpen(false);
  };

  return (
    <div className="db-layout">
      <DashboardHeader />
      <div className="db-shell">
        <DashboardSidebar active={active} onSelect={setActive} />
        <main className="db-main profile-page">
          <div className="profile-top-bar">
            <div className="db-welcome">
              <h2>Profile</h2>
              <p>Manage your freelancer profile and preferences</p>
            </div>
            <button className="db-primary edit-btn" onClick={() => setIsEditModalOpen(true)}>
              <span className="btn-icon">✎</span> Edit Profile
            </button>
          </div>

          <ProfileCompletionCard completion={profile.completion} />

          <div className="profile-content-card">
            <ProfileHeader profile={profile} />
            <ProfileDetails profile={profile} onToggleAvailability={(val) => setProfile(prev => ({...prev, availability: val}))} />
            
            <div className="profile-section-divider" />
            
            <CategoryDynamicSection profile={profile} />
            
            <div className="profile-section-divider" />
            
            <PortfolioPreview portfolio={profile.portfolio} />
          </div>
        </main>
      </div>

      {isEditModalOpen && (
        <EditProfileModal 
          profile={profile} 
          onClose={() => setIsEditModalOpen(false)} 
          onSave={handleUpdateProfile} 
        />
      )}
    </div>
  );
}
