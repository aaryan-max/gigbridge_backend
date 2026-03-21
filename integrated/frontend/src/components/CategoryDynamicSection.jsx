import React from "react";

const CATEGORY_FIELDS = {
  "Dance": {
    title: "Dance Performance Details",
    fields: [
      { label: "Dance Style", key: "danceStyle", value: "Hip Hop, Contemporary" },
      { label: "Performance Type", key: "performanceType", value: "Solo, Group" }
    ]
  },
  "Photography": {
    title: "Photography Gear & Experience",
    fields: [
      { label: "Photography Type", key: "photographyType", value: "Wedding, Portrait" },
      { label: "Equipment Used", key: "equipment", value: "Sony A7R IV, Canon EOS R5" }
    ]
  },
  "Designer": {
    title: "Design Specialization",
    fields: [
      { label: "Design Tools", key: "designTools", value: "Figma, Adobe XD, Photoshop" },
      { label: "Specializations", key: "specializations", value: "UI Design, Branding" }
    ]
  },
  "Musician": {
    title: "Musical Performance",
    fields: [
      { label: "Instruments", key: "instruments", value: "Guitar, Piano" },
      { label: "Genre", key: "genre", value: "Jazz, Blues" }
    ]
  }
};

export default function CategoryDynamicSection({ profile }) {
  const categoryData = CATEGORY_FIELDS[profile.category] || { 
    title: "Professional Details", 
    fields: [{ label: "Experience", key: "experience", value: `${profile.experience} years` }] 
  };

  return (
    <div className="category-dynamic-section">
      <h3 className="section-title">{categoryData.title}</h3>
      <div className="profile-details-grid" style={{ padding: 0 }}>
        <div className="detail-col">
          {categoryData.fields.map(field => (
            <div key={field.key} className="detail-item">
              <span className="detail-label">{field.label}</span>
              <span className="detail-value">{field.value}</span>
            </div>
          ))}
          <div className="detail-item">
            <span className="detail-label">Experience</span>
            <span className="detail-value">{profile.experience} years</span>
          </div>
        </div>
        
        <div className="detail-col">
          <div className="detail-item">
            <span className="detail-label">Skills / Specializations</span>
            <div className="skills-tags">
              {profile.skills.map(skill => (
                <span key={skill} className="skill-tag">{skill}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
