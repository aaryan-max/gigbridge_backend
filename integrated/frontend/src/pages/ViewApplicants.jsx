import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import "./ViewApplicants.css";

export default function ViewApplicants() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { user } = useAuth();
  
  const [project, setProject] = useState(null);
  const [applicants, setApplicants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjectAndApplicants();
  }, [id]);

  const fetchProjectAndApplicants = () => {
    // Mock data - no API integration needed
    setTimeout(() => {
      const mockProjects = {
        1: {
          id: 1,
          category: "Web Design",
          location: "New York",
          pincode: "10001",
          description: "Looking for an experienced web designer to create a modern e-commerce website.",
          budget: "5000",
          deadline: "2024-04-15",
          applicants: [
            { 
              id: 1, 
              name: "Sarah Johnson", 
              category: "Web Design", 
              bio: "5+ years of experience in web development with expertise in React, Vue, and modern CSS frameworks. Passionate about creating user-friendly interfaces.",
              rating: 4.8, 
              image: "https://picsum.photos/seed/sarah/80/80.jpg",
              location: "New York",
              hourlyRate: 75,
              skills: ["React", "Vue", "CSS", "JavaScript", "UI/UX"],
              completedProjects: 42,
              responseTime: "Within 2 hours"
            },
            { 
              id: 2, 
              name: "Mike Chen", 
              category: "UI/UX Design", 
              bio: "Specialized in modern UI design with a focus on user experience. Worked with Fortune 500 companies and startups alike.",
              rating: 4.9, 
              image: "https://picsum.photos/seed/mike/80/80.jpg",
              location: "San Francisco",
              hourlyRate: 85,
              skills: ["UI Design", "UX Research", "Figma", "Prototyping"],
              completedProjects: 38,
              responseTime: "Within 1 hour"
            },
            { 
              id: 3, 
              name: "Lisa Anderson", 
              category: "Web Design", 
              bio: "Full-stack developer with 7+ years of experience. Expert in e-commerce solutions and payment integrations.",
              rating: 4.7, 
              image: "https://picsum.photos/seed/lisa/80/80.jpg",
              location: "Los Angeles",
              hourlyRate: 80,
              skills: ["Node.js", "MongoDB", "E-commerce", "Payment APIs"],
              completedProjects: 56,
              responseTime: "Within 3 hours"
            }
          ],
          selectedApplicant: null,
          status: "pending"
        },
        2: {
          id: 2,
          category: "Mobile App Development",
          location: "San Francisco",
          pincode: "94102",
          description: "Need a skilled mobile app developer for iOS and Android platforms.",
          budget: "8000",
          deadline: "2024-05-01",
          applicants: [],
          selectedApplicant: null,
          status: "pending"
        },
        3: {
          id: 3,
          category: "Graphic Design",
          location: "Los Angeles",
          pincode: "90001",
          description: "Creative graphic designer needed for branding project.",
          budget: "3000",
          deadline: "2024-03-30",
          applicants: [
            { 
              id: 4, 
              name: "Emily Davis", 
              category: "Graphic Design", 
              bio: "10+ years in branding and design. Creative professional with expertise in logo design, brand identity, and marketing materials.",
              rating: 4.7, 
              image: "https://picsum.photos/seed/emily/80/80.jpg",
              location: "Los Angeles",
              hourlyRate: 65,
              skills: ["Branding", "Logo Design", "Adobe Creative Suite", "Marketing"],
              completedProjects: 89,
              responseTime: "Within 4 hours"
            }
          ],
          selectedApplicant: null,
          status: "pending"
        },
        4: {
          id: 4,
          category: "Content Writing",
          location: "Chicago",
          pincode: "60601",
          description: "Professional content writer for blog and social media.",
          budget: "2000",
          deadline: "2024-04-10",
          applicants: [
            { 
              id: 5, 
              name: "Alex Wilson", 
              category: "Content Writing", 
              bio: "Expert in SEO and content strategy. Professional writer with experience in various industries and content types.",
              rating: 4.9, 
              image: "https://picsum.photos/seed/alex/80/80.jpg",
              location: "Chicago",
              hourlyRate: 50,
              skills: ["SEO Writing", "Content Strategy", "Blog Writing", "Social Media"],
              completedProjects: 124,
              responseTime: "Within 1 hour"
            }
          ],
          selectedApplicant: { 
            id: 5, 
            name: "Alex Wilson", 
            category: "Content Writing", 
            bio: "Expert in SEO and content strategy. Professional writer with experience in various industries and content types.",
            rating: 4.9, 
            image: "https://picsum.photos/seed/alex/80/80.jpg",
            location: "Chicago",
            hourlyRate: 50,
            skills: ["SEO Writing", "Content Strategy", "Blog Writing", "Social Media"],
            completedProjects: 124,
            responseTime: "Within 1 hour"
          },
          status: "accepted"
        }
      };

      const projectData = mockProjects[id];
      if (projectData) {
        setProject(projectData);
        setApplicants(projectData.applicants || []);
      }
      setLoading(false);
    }, 800);
  };

  const handleAccept = (applicant) => {
    // Update local state
    setProject(prev => ({
      ...prev,
      selectedApplicant: applicant,
      status: "accepted"
    }));
    
    // Remove applicant from list
    setApplicants(prev => prev.filter(app => app.id !== applicant.id));
    
    alert(`Applicant ${applicant.name} has been selected for this project!`);
  };

  const handleReject = (applicantId) => {
    // Remove applicant from list
    setApplicants(prev => prev.filter(app => app.id !== applicantId));
    
    alert("Applicant has been rejected.");
  };

  const handleGoBack = () => {
    navigate("/my-projects");
  };

  const handleMessageArtist = (artistId) => {
    navigate(`/messages?artist=${artistId}`);
  };

  const viewPortfolio = (artist) => {
    // Mock portfolio view
    alert(`Viewing portfolio for ${artist.name}`);
  };

  if (!user.isAuthenticated) {
    navigate("/login/client");
    return null;
  }

  if (loading) {
    return (
      <div className="view-applicants-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading project details...</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="view-applicants-container">
        <div className="error-state">
          <h3>Project Not Found</h3>
          <p>The project you're looking for doesn't exist.</p>
          <button onClick={handleGoBack} className="back-btn">Back to My Projects</button>
        </div>
      </div>
    );
  }

  return (
    <div className="view-applicants-container">
      <div className="applicants-header">
        <button className="back-btn" onClick={handleGoBack}>
          ← Back to My Projects
        </button>
        <div className="project-info">
          <h1>Applicants for {project.category}</h1>
          <p>{project.location}, {project.pincode}</p>
          {project.budget && (
            <span className="budget-badge">💰 Budget: ${project.budget}</span>
          )}
        </div>
      </div>

      <div className="project-description">
        <h3>Project Description</h3>
        <p>{project.description}</p>
        {project.deadline && (
          <p className="deadline">📅 Deadline: {new Date(project.deadline).toLocaleDateString()}</p>
        )}
      </div>

      {applicants.length === 0 && !project.selectedApplicant ? (
        <div className="no-applicants">
          <h3>No applicants available</h3>
          <p>All applicants have been reviewed or no one has applied yet.</p>
        </div>
      ) : (
        <div className="applicants-list">
          <h2>Applicants ({applicants.length})</h2>
          {applicants.map(applicant => (
            <div key={applicant.id} className="applicant-card">
              <div className="applicant-header">
                <img 
                  src={applicant.image} 
                  alt={applicant.name}
                  className="applicant-image"
                />
                <div className="applicant-info">
                  <h3>{applicant.name}</h3>
                  <p className="applicant-category">{applicant.category}</p>
                  <div className="applicant-meta">
                    <div className="applicant-rating">
                      ⭐ {applicant.rating}
                    </div>
                    <div className="applicant-location">
                      📍 {applicant.location}
                    </div>
                    {applicant.hourlyRate > 0 && (
                      <div className="applicant-rate">
                        💲 ${applicant.hourlyRate}/hr
                      </div>
                    )}
                  </div>
                </div>
                <div className="applicant-stats">
                  <div className="stat">
                    <span className="stat-number">{applicant.completedProjects}</span>
                    <span className="stat-label">Projects</span>
                  </div>
                  <div className="stat">
                    <span className="stat-number">{applicant.responseTime}</span>
                    <span className="stat-label">Response</span>
                  </div>
                </div>
              </div>
              
              <div className="applicant-bio">
                <p>{applicant.bio}</p>
              </div>

              {applicant.skills && applicant.skills.length > 0 && (
                <div className="applicant-skills">
                  <h4>Skills</h4>
                  <div className="skills-list">
                    {applicant.skills.slice(0, 5).map((skill, index) => (
                      <span key={index} className="skill-tag">{skill}</span>
                    ))}
                    {applicant.skills.length > 5 && (
                      <span className="skill-more">+{applicant.skills.length - 5} more</span>
                    )}
                  </div>
                </div>
              )}
              
              <div className="applicant-actions">
                <button 
                  className="accept-btn"
                  onClick={() => handleAccept(applicant)}
                >
                  Accept
                </button>
                <button 
                  className="reject-btn"
                  onClick={() => handleReject(applicant.id)}
                >
                  Reject
                </button>
                <button 
                  className="message-btn"
                  onClick={() => handleMessageArtist(applicant.id)}
                >
                  Message
                </button>
                <button 
                  className="portfolio-btn"
                  onClick={() => viewPortfolio(applicant)}
                >
                  View Portfolio
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {project.selectedApplicant && (
        <div className="selected-notice">
          <h3>✓ Selected Applicant</h3>
          <div className="selected-artist-info">
            <img src={project.selectedApplicant.image} alt={project.selectedApplicant.name} />
            <div>
              <p><strong>{project.selectedApplicant.name}</strong> has been chosen for this project.</p>
              <p className="selected-category">{project.selectedApplicant.category}</p>
            </div>
          </div>
          <div className="selected-actions">
            <button className="message-btn" onClick={() => handleMessageArtist(project.selectedApplicant.id)}>
              Message Artist
            </button>
            <button className="back-btn" onClick={handleGoBack}>
              Back to My Projects
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
