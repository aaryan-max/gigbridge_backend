import React, { useState } from 'react';

const CATEGORIES = ["Designer", "Dance", "Photography", "Musician", "Artist", "Event Organizer"];

export default function AddProjectModal({ onClose, onSave }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'Designer',
    tags: '',
    image: '',
    link: ''
  });
  const [preview, setPreview] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
        setFormData(prev => ({ ...prev, image: reader.result }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const tagsArray = formData.tags.split(',').map(t => t.trim()).filter(t => t !== '');
    onSave({
      ...formData,
      tags: tagsArray,
      image: formData.image || 'https://images.unsplash.com/photo-1557821552-17105176677c?w=500' // Fallback
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="add-project-modal" onClick={e => e.stopPropagation()}>
        <header className="modal-header">
          <h3>Add New Project</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </header>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>Project Title</label>
            <input 
              name="title" 
              placeholder="e.g. Modern E-commerce Website" 
              value={formData.title}
              onChange={handleChange}
              required 
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea 
              name="description" 
              placeholder="Tell clients what you did and how it helped..." 
              value={formData.description}
              onChange={handleChange}
              rows={4}
              required 
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Category</label>
              <select name="category" value={formData.category} onChange={handleChange}>
                {CATEGORIES.map(cat => <option key={cat} value={cat}>{cat}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Skill Tags (comma separated)</label>
              <input 
                name="tags" 
                placeholder="React, UI Design, Figma" 
                value={formData.tags}
                onChange={handleChange}
                required 
              />
            </div>
          </div>

          <div className="form-group">
            <label>Thumbnail Image</label>
            {preview ? (
              <div className="preview-container">
                <img src={preview} alt="Project Preview" />
                <button type="button" className="remove-preview" onClick={() => setPreview(null)}>
                  &times;
                </button>
              </div>
            ) : (
              <label className="image-dropzone">
                <div style={{ fontSize: '32px', marginBottom: '8px' }}>📸</div>
                <div style={{ fontWeight: 500, color: '#2563eb' }}>Click to upload thumbnail</div>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>PNG, JPG or JPEG (Max 5MB)</div>
                <input type="file" accept="image/*" style={{ display: 'none' }} onChange={handleImageUpload} />
              </label>
            )}
          </div>

          <div className="form-group">
            <label>Project Link (Optional)</label>
            <input 
              name="link" 
              placeholder="https://yourproject.com" 
              value={formData.link}
              onChange={handleChange}
            />
          </div>
        </form>

        <footer className="modal-footer">
          <button type="button" className="secondary-btn" onClick={onClose}>Cancel</button>
          <button type="submit" className="db-primary" onClick={handleSubmit}>Post Project</button>
        </footer>
      </div>
    </div>
  );
}
