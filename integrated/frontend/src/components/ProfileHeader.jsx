import React from "react";

export default function ProfileHeader({ profile }) {
  const initials = profile.name.split(' ').map(n => n[0]).join('').toUpperCase();

  return (
    <div className="profile-header-container">
      <div className="profile-header-banner">
        <div className="profile-avatar-wrap">
          <div className="profile-avatar-large">
            {profile.profileImage ? (
              <img src={profile.profileImage} alt={profile.name} />
            ) : (
              initials
            )}
          </div>
        </div>
      </div>
      <div className="profile-info-summary">
        <h1>{profile.name}</h1>
        <p>{profile.category || "Freelancer"}</p>
        <p className="profile-location">📍 {profile.location}</p>
      </div>
    </div>
  );
}
