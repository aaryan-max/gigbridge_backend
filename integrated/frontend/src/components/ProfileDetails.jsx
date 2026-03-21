import React from "react";

export default function ProfileDetails({ profile, onToggleAvailability }) {
  return (
    <div className="profile-details-grid">
      <div className="detail-col">
        <div className="detail-item">
          <span className="detail-label">Full Name</span>
          <span className="detail-value">{profile.name}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Phone</span>
          <span className="detail-value">{profile.phone}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Hourly Rate</span>
          <span className="detail-value">₹{profile.hourlyRate}/hour</span>
        </div>
        <div className="detail-item full-width">
          <span className="detail-label">Bio</span>
          <span className="detail-value bio">{profile.bio}</span>
        </div>
      </div>
      
      <div className="detail-col">
        <div className="detail-item">
          <span className="detail-label">Email</span>
          <span className="detail-value">{profile.email}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Location</span>
          <span className="detail-value">{profile.location}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Availability</span>
          <div className="availability-toggle" onClick={() => onToggleAvailability(!profile.availability)}>
            <div className={`toggle-switch ${profile.availability ? 'on' : ''}`}>
              <div className="toggle-knob" />
            </div>
            <span className="availability-status">
              {profile.availability ? "Available for work" : "Not available"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
