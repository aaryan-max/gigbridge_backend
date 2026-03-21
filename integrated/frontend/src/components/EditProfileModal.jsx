import React, { useState } from "react";

const CATEGORIES = ["Dance", "Photography", "Designer", "Musician", "Artist", "Event Organizer"];

export default function EditProfileModal({ profile, onClose, onSave }) {
  const [formData, setFormData] = useState({ ...profile });
  const [imagePreview, setImagePreview] = useState(profile.profileImage);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
        setFormData(prev => ({ ...prev, profileImage: reader.result }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSave = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="edit-modal" onClick={e => e.stopPropagation()}>
        <header className="modal-header">
          <h3>Edit Profile</h3>
          <button className="close-modal" onClick={onClose}>&times;</button>
        </header>
        
        <form className="modal-body" onSubmit={handleSave}>
          <div className="form-group full-width">
            <label>Profile Image</label>
            <div className="image-upload-wrap">
              <div className="upload-preview">
                {imagePreview ? (
                  <img src={imagePreview} alt="Preview" />
                ) : (
                  <span style={{ fontSize: '24px', color: '#94a3b8' }}>👤</span>
                )}
              </div>
              <label htmlFor="imageUpload" className="upload-btn-label">Change Image</label>
              <input 
                id="imageUpload" 
                type="file" 
                accept="image/*" 
                onChange={handleImageChange} 
                style={{ display: 'none' }} 
              />
            </div>
          </div>

          <div className="form-group">
            <label>Full Name</label>
            <input 
              name="name" 
              value={formData.name} 
              onChange={handleInputChange} 
              required 
            />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input 
              name="email" 
              type="email" 
              value={formData.email} 
              onChange={handleInputChange} 
              required 
            />
          </div>

          <div className="form-group">
            <label>Phone</label>
            <input 
              name="phone" 
              value={formData.phone} 
              onChange={handleInputChange} 
            />
          </div>

          <div className="form-group">
            <label>Location</label>
            <input 
              name="location" 
              value={formData.location} 
              onChange={handleInputChange} 
            />
          </div>

          <div className="form-group">
            <label>Hourly Rate (₹)</label>
            <input 
              name="hourlyRate" 
              type="number" 
              value={formData.hourlyRate} 
              onChange={handleInputChange} 
            />
          </div>

          <div className="form-group">
            <label>Category</label>
            <select name="category" value={formData.category} onChange={handleInputChange}>
              {CATEGORIES.map(cat => <option key={cat} value={cat}>{cat}</option>)}
            </select>
          </div>

          <div className="form-group full-width">
            <label>Bio</label>
            <textarea 
              name="bio" 
              value={formData.bio} 
              onChange={handleInputChange} 
            />
          </div>

          <div className="form-group full-width">
            <label>Skills (comma separated)</label>
            <input 
              name="skills" 
              value={formData.skills.join(', ')} 
              onChange={(e) => setFormData(prev => ({
                ...prev, 
                skills: e.target.value.split(',').map(s => s.trim()).filter(s => s)
              }))} 
            />
          </div>

          {/* Dynamic category specific fields could go here */}
          {formData.category === "Dance" && (
            <div className="form-group full-width">
              <label>Dance Style</label>
              <input name="danceStyle" placeholder="e.g. Hip Hop, Contemporary" />
            </div>
          )}

          <div className="form-group">
            <label>Availability</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', height: '100%' }}>
              <input 
                type="checkbox" 
                name="availability" 
                checked={formData.availability} 
                onChange={handleInputChange} 
                style={{ width: '20px', height: '20px' }}
              />
              <span style={{ fontSize: '14px', color: '#475569' }}>Available for work</span>
            </div>
          </div>
        </form>

        <footer className="modal-footer">
          <button className="cancel-btn" onClick={onClose}>Cancel</button>
          <button className="save-btn" onClick={handleSave}>Save Profile</button>
        </footer>
      </div>
    </div>
  );
}
