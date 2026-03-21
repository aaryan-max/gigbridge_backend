import { useState } from 'react';
import DashboardHeader from '../components/DashboardHeader';
import DashboardSidebar from '../components/DashboardSidebar';
import { User, Lock, Bell, Shield, Eye, EyeOff, Mail, Phone, Globe, AlertTriangle } from 'lucide-react';
import './settings.css';

const SettingsPage = () => {
  const [activeSidebar, setActiveSidebar] = useState('settings');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  
  // Form states
  const [email, setEmail] = useState('john.smith@example.com');
  const [phone, setPhone] = useState('+91 9876543210');
  const [language, setLanguage] = useState('English');
  const [currentPassword, setCurrentPassword] = useState('password123');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Notification toggles
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [projectUpdates, setProjectUpdates] = useState(true);
  const [messageAlerts, setMessageAlerts] = useState(true);
  const [jobMatchAlerts, setJobMatchAlerts] = useState(false);
  const [twoFactorAuth, setTwoFactorAuth] = useState(false);

  const handleSaveChanges = () => {
    // Mock save action
    console.log('Settings saved:', {
      email, phone, language, currentPassword, newPassword, confirmPassword,
      emailNotifications, pushNotifications, projectUpdates, messageAlerts, jobMatchAlerts, twoFactorAuth
    });
    alert('Settings saved successfully!');
  };

  const handleDeleteAccount = () => {
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = () => {
    // Mock delete action
    console.log('Account deleted permanently');
    setShowDeleteModal(false);
    alert('Account deleted successfully');
  };

  return (
    <div className="db-layout">
      <DashboardHeader />
      <div className="db-shell">
        <DashboardSidebar active={activeSidebar} onSelect={setActiveSidebar} />
        <main className="db-main settings-page">
          {/* Page Header */}
          <div className="settings-header">
            <h2>Settings</h2>
            <p>Manage your account settings and preferences</p>
          </div>

          {/* Settings Cards Container - Single Column */}
          <div className="settings-container">
            {/* Block 1: Account Settings */}
            <div className="settings-card">
              <div className="card-header">
                <User className="card-icon" />
                <h3>Account Settings</h3>
              </div>
              <div className="card-content">
                <div className="form-group">
                  <label className="form-label">
                    <Mail className="label-icon" />
                    Email Address
                  </label>
                  <input
                    type="email"
                    className="form-input"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label">
                    <Phone className="label-icon" />
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    className="form-input"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label">
                    <Globe className="label-icon" />
                    Language
                  </label>
                  <select
                    className="form-select"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                  >
                    <option value="English">English</option>
                    <option value="Spanish">Spanish</option>
                    <option value="French">French</option>
                    <option value="German">German</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Block 2: Security Settings */}
            <div className="settings-card">
              <div className="card-header">
                <Lock className="card-icon" />
                <h3>Security</h3>
              </div>
              <div className="card-content">
                <div className="form-group">
                  <label className="form-label">Current Password</label>
                  <div className="password-input-container">
                    <input
                      type={showCurrentPassword ? "text" : "password"}
                      className="form-input"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    >
                      {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                
                <div className="form-group">
                  <label className="form-label">New Password</label>
                  <div className="password-input-container">
                    <input
                      type={showNewPassword ? "text" : "password"}
                      className="form-input"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                    >
                      {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                
                <div className="form-group">
                  <label className="form-label">Confirm New Password</label>
                  <div className="password-input-container">
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      className="form-input"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                
                <div className="divider"></div>
                
                <div className="form-group">
                  <label className="form-label">Two-Factor Authentication</label>
                  <div className="toggle-container">
                    <span className="toggle-description">Add an extra layer of security to your account</span>
                    <button
                      className={`toggle-switch ${twoFactorAuth ? 'active' : ''}`}
                      onClick={() => setTwoFactorAuth(!twoFactorAuth)}
                    >
                      <div className="toggle-slider"></div>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Block 3: Notification Settings */}
            <div className="settings-card">
              <div className="card-header">
                <Bell className="card-icon" />
                <h3>Notifications</h3>
              </div>
              <div className="card-content">
                <div className="toggle-group">
                  {[
                    { key: 'email', label: 'Email Notifications', state: emailNotifications, setter: setEmailNotifications },
                    { key: 'push', label: 'Push Notifications', state: pushNotifications, setter: setPushNotifications },
                    { key: 'project', label: 'Project Updates', state: projectUpdates, setter: setProjectUpdates },
                    { key: 'message', label: 'Message Alerts', state: messageAlerts, setter: setMessageAlerts },
                    { key: 'job', label: 'Job Match Alerts', state: jobMatchAlerts, setter: setJobMatchAlerts }
                  ].map((item) => (
                    <div key={item.key} className="toggle-item">
                      <span className="toggle-label">{item.label}</span>
                      <button
                        className={`toggle-switch ${item.state ? 'active' : ''}`}
                        onClick={() => item.setter(!item.state)}
                      >
                        <div className="toggle-slider"></div>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Block 4: Danger Zone */}
            <div className="settings-card">
              <div className="card-header">
                <Shield className="card-icon danger" />
                <h3>Danger Zone</h3>
              </div>
              <div className="card-content">
                <p>Once you delete your account, there is no going back. Please be certain.</p>
                <button className="btn-danger" onClick={handleDeleteAccount}>Delete Account</button>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="settings-actions">
            <button className="btn-secondary">Cancel</button>
            <button className="btn-primary" onClick={handleSaveChanges}>Save Changes</button>
          </div>

          {/* Delete Account Modal */}
          {showDeleteModal && (
            <div className="modal-overlay" onClick={() => setShowDeleteModal(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>Delete Account</h3>
                  <button className="modal-close" onClick={() => setShowDeleteModal(false)}>
                    ×
                  </button>
                </div>
                <div className="modal-body">
                  <p>Are you sure you want to delete your account? This action cannot be undone.</p>
                </div>
                <div className="modal-footer">
                  <button className="btn-secondary" onClick={() => setShowDeleteModal(false)}>Cancel</button>
                  <button className="btn-danger" onClick={handleConfirmDelete}>Delete Permanently</button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default SettingsPage;
