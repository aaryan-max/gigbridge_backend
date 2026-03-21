import { useState, useEffect } from 'react';
import DashboardHeader from '../components/DashboardHeader';
import DashboardSidebar from '../components/DashboardSidebar';
import { Shield, CheckCircle, FileText, Upload } from 'lucide-react';
import './verification.css';

const VerificationPage = () => {
  const [activeSidebar, setActiveSidebar] = useState('verification');
  const [verificationSteps, setVerificationSteps] = useState([
    {
      id: 1,
      title: 'Identity Verification',
      description: 'Upload government-issued ID',
      status: 'Not Submitted',
      uploadedFile: null
    },
    {
      id: 2,
      title: 'Address Proof',
      description: 'Upload utility bill or bank statement',
      status: 'Not Submitted',
      uploadedFile: null
    },
    {
      id: 3,
      title: 'Professional Verification',
      description: 'Upload certifications or portfolio proof',
      status: 'Not Submitted',
      uploadedFile: null
    }
  ]);

  const [draggedStep, setDraggedStep] = useState(null);

  const getCompletedSteps = () => {
    return verificationSteps.filter(step => step.status === 'Verified').length;
  };

  const getProgressPercentage = () => {
    const completed = getCompletedSteps();
    return (completed / 3) * 100;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Verified':
        return 'bg-green-100 text-green-700';
      case 'Pending Review':
        return 'bg-yellow-100 text-yellow-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const handleFileUpload = (stepId, file) => {
    setVerificationSteps(prev => 
      prev.map(step => 
        step.id === stepId 
          ? { 
              ...step, 
              status: 'Pending Review',
              uploadedFile: file
            }
          : step
      )
    );
  };

  const handleDragOver = (e, stepId) => {
    e.preventDefault();
    setDraggedStep(stepId);
  };

  const handleDragLeave = () => {
    setDraggedStep(null);
  };

  const handleDrop = (e, stepId) => {
    e.preventDefault();
    setDraggedStep(null);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(stepId, files[0]);
    }
  };

  const handleFileSelect = (e, stepId) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFileUpload(stepId, files[0]);
    }
  };

  return (
    <div className="db-layout">
      <DashboardHeader />
      <div className="db-shell">
        <DashboardSidebar active={activeSidebar} onSelect={setActiveSidebar} />
        <main className="db-main verification-page">
          {/* Page Header */}
          <div className="verification-header">
            <h2>Verification</h2>
            <p>Complete your profile verification to unlock all features</p>
          </div>

          {/* Verification Status Card */}
          <div className="verification-status-card">
            <div className="status-left">
              <div className="status-icon">
                <Shield className="w-8 h-8 text-blue-600" />
              </div>
              <div className="status-text">
                <h3>Verification Status</h3>
                <p>{getCompletedSteps()} of 3 steps completed</p>
              </div>
            </div>
            <div className="status-progress">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${getProgressPercentage()}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Why Verify Section */}
          <div className="why-verify-section">
            <h3>Why Verify Your Account</h3>
            <div className="info-cards">
              <div className="info-card">
                <CheckCircle className="w-8 h-8 text-green-600" />
                <h4>Build Trust</h4>
                <p>Stand out to clients with verified badge</p>
              </div>
              <div className="info-card">
                <Shield className="w-8 h-8 text-blue-600" />
                <h4>Secure Payments</h4>
                <p>Access protected payment methods</p>
              </div>
              <div className="info-card">
                <FileText className="w-8 h-8 text-purple-600" />
                <h4>Premium Projects</h4>
                <p>Apply for high-value event bookings</p>
              </div>
            </div>
          </div>

          {/* Verification Steps */}
          <div className="verification-steps">
            <h3>Verification Steps</h3>
            <div className="steps-grid">
              {verificationSteps.map(step => (
                <div key={step.id} className="step-card">
                  <div className="step-header">
                    <div className="step-info">
                      <div className="step-number">{step.id}</div>
                      <div>
                        <h4>{step.title}</h4>
                        <p>{step.description}</p>
                      </div>
                    </div>
                    <div className={`step-status ${getStatusColor(step.status)}`}>
                      {step.status}
                    </div>
                  </div>
                  
                  {/* Upload Area */}
                  <div 
                    className={`upload-area ${draggedStep === step.id ? 'drag-over' : ''}`}
                    onDragOver={(e) => handleDragOver(e, step.id)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, step.id)}
                  >
                    <Upload className="w-8 h-8 text-gray-400 mb-2" />
                    <p className="upload-text">Click to upload or drag and drop</p>
                    <p className="upload-subtext">PDF, JPG or PNG (max 10MB)</p>
                    <input
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={(e) => handleFileSelect(e, step.id)}
                      className="file-input"
                    />
                  </div>
                  
                  {/* Show uploaded file info */}
                  {step.uploadedFile && (
                    <div className="uploaded-file">
                      <FileText className="w-4 h-4 text-green-600" />
                      <span>{step.uploadedFile.name}</span>
                    </div>
                  )}

                  {/* Professional verification examples */}
                  {step.id === 3 && (
                    <div className="examples-section">
                      <h5>Examples for GigBridge artists:</h5>
                      <ul>
                        <li>Dance certification</li>
                        <li>Music performance certificate</li>
                        <li>Photography portfolio</li>
                        <li>Event performance proof</li>
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default VerificationPage;
