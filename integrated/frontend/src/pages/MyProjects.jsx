import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import "./MyProjects.css";

export default function MyProjects() {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Mock project data with artists - no API integration needed
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate loading and set mock data
    setTimeout(() => {
      setProjects([
        {
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
              bio: "5+ years of experience in web development", 
              rating: 4.8, 
              image: "https://picsum.photos/seed/sarah/80/80.jpg" 
            },
            { 
              id: 2, 
              name: "Mike Chen", 
              category: "UI/UX Design", 
              bio: "Specialized in modern UI design", 
              rating: 4.9, 
              image: "https://picsum.photos/seed/mike/80/80.jpg" 
            }
          ],
          selectedApplicant: null,
          status: "pending"
        },
        {
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
        {
          id: 3,
          category: "Graphic Design",
          location: "Los Angeles",
          pincode: "90001",
          description: "Creative graphic designer needed for branding project.",
          budget: "3000",
          deadline: "2024-03-30",
          applicants: [
            { 
              id: 3, 
              name: "Emily Davis", 
              category: "Graphic Design", 
              bio: "10+ years in branding and design", 
              rating: 4.7, 
              image: "https://picsum.photos/seed/emily/80/80.jpg" 
            }
          ],
          selectedApplicant: null,
          status: "pending"
        },
        {
          id: 4,
          category: "Content Writing",
          location: "Chicago",
          pincode: "60601",
          description: "Professional content writer for blog and social media.",
          budget: "2000",
          deadline: "2024-04-10",
          applicants: [
            { 
              id: 4, 
              name: "Alex Wilson", 
              category: "Content Writing", 
              bio: "Expert in SEO and content strategy", 
              rating: 4.9, 
              image: "https://picsum.photos/seed/alex/80/80.jpg" 
            }
          ],
          selectedApplicant: { 
            id: 4, 
            name: "Alex Wilson", 
            category: "Content Writing", 
            bio: "Expert in SEO and content strategy", 
            rating: 4.9, 
            image: "https://picsum.photos/seed/alex/80/80.jpg" 
          },
          status: "accepted"
        },
        {
          id: 5,
          category: "Video Editing",
          location: "Miami",
          pincode: "33101",
          description: "Professional video editor for YouTube content.",
          budget: "4000",
          deadline: "2024-04-20",
          applicants: [],
          selectedApplicant: null,
          status: "completed"
        }
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const handleViewApplicants = (projectId) => {
    navigate(`/project/${projectId}/applicants`);
  };

  const handleAcceptApplicant = (projectId, applicant) => {
    setProjects(prev => prev.map(project => 
      project.id === projectId 
        ? { ...project, selectedApplicant: applicant, status: "accepted", applicants: project.applicants.filter(app => app.id !== applicant.id) }
        : project
    ));
    
    alert(`Applicant ${applicant.name} has been selected for this project!`);
  };

  const handleRejectApplicant = (projectId, applicantId) => {
    setProjects(prev => prev.map(project => 
      project.id === projectId 
        ? { ...project, applicants: project.applicants.filter(app => app.id !== applicantId) }
        : project
    ));
    
    alert("Applicant has been rejected.");
  };

  const getStatusBadge = (project) => {
    if (project.status === "completed") {
      return { text: "Completed", color: "gray" };
    }
    if (project.selectedApplicant) {
      return { text: "Accepted", color: "green" };
    }
    if (project.applicants && project.applicants.length > 0) {
      return { text: "Ongoing", color: "blue" };
    }
    return { text: "Pending", color: "yellow" };
  };

  const getBottomContent = (project) => {
    if (project.status === "completed") {
      return <span className="status-text completed">✔ Project Completed</span>;
    }
    if (project.selectedApplicant) {
      return (
        <div className="accepted-info">
          <span className="status-text accepted">✔ Applicant Chosen</span>
          <div className="selected-artist">
            <img src={project.selectedApplicant.image} alt={project.selectedApplicant.name} />
            <span>{project.selectedApplicant.name}</span>
          </div>
        </div>
      );
    }
    if (project.applicants && project.applicants.length > 0) {
      return (
        <div className="applicants-preview">
          <div className="applicants-avatars">
            {project.applicants.slice(0, 3).map(applicant => (
              <img key={applicant.id} src={applicant.image} alt={applicant.name} title={applicant.name} />
            ))}
            {project.applicants.length > 3 && (
              <span className="more-count">+{project.applicants.length - 3}</span>
            )}
          </div>
          <button 
            className="view-applicants-btn"
            onClick={() => handleViewApplicants(project.id)}
          >
            View {project.applicants.length} Applicant{project.applicants.length > 1 ? 's' : ''}
          </button>
        </div>
      );
    }
    return <span className="status-text pending">⏳ No Applicants Yet</span>;
  };

  if (!user.isAuthenticated) {
    navigate("/login/client");
    return null;
  }

  if (loading) {
    return (
      <div className="my-projects-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading your projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="my-projects-container">
      <div className="my-projects-header">
        <h1>My Projects</h1>
        <p>Manage and track your posted projects</p>
      </div>

      {projects.length === 0 ? (
        <div className="empty-state">
          <h3>No projects posted yet</h3>
          <p>Start by posting your first project to connect with talented artists</p>
          <button 
            className="post-project-btn"
            onClick={() => navigate("/client/post-project")}
          >
            Post a Project
          </button>
        </div>
      ) : (
        <div className="projects-grid">
          {projects.map(project => {
            const statusBadge = getStatusBadge(project);
            return (
              <div key={project.id} className="project-card">
                <div className="card-header">
                  <h3>{project.category}</h3>
                  <span className={`status-badge ${statusBadge.color}`}>
                    {statusBadge.text}
                  </span>
                </div>
                
                <div className="location-info">
                  <span>📍 {project.location}, {project.pincode}</span>
                </div>
                
                <p className="description">{project.description}</p>
                
                <div className="project-meta">
                  {project.budget && (
                    <span className="budget">💰 ${project.budget}</span>
                  )}
                  {project.deadline && (
                    <span className="deadline">📅 {new Date(project.deadline).toLocaleDateString()}</span>
                  )}
                </div>
                
                <div className="card-footer">
                  {getBottomContent(project)}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
