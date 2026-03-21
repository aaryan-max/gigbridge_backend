import React, { useState, useMemo } from 'react';
import DashboardHeader from '../components/DashboardHeader';
import DashboardSidebar from '../components/DashboardSidebar';
import RecommendedProjects from '../components/RecommendedProjects';
import HireRequestCard from '../components/HireRequestCard';
import ProjectCard from '../components/ProjectCard';
import ProposalModal from '../components/ProposalModal';
import FilterPanel from '../components/FilterPanel';
import EmptyStateOpportunities from '../components/EmptyStateOpportunities';
import { useAuth } from '../context/AuthContext';
import './dashboard.css';
import './opportunities.css';

const MOCK_USER = {
  category: 'Designer',
  skills: ['React', 'UI/UX', 'Figma', 'Tailwind CSS'],
  experience: 'Intermediate'
};

const MOCK_HIRE_REQUESTS = [
  {
    id: 'hr1',
    title: "E-commerce Website Redesign",
    client: "Sarah Johnson",
    avatar: "SJ",
    rating: 4.8,
    description: "Looking for an experienced frontend developer to redesign our e-commerce platform with a focus on conversion and mobile responsiveness.",
    budget: "$5,000 - $8,000",
    timeline: "2-3 months",
    location: "Remote",
    skills: ["React", "TypeScript", "Tailwind CSS"],
    category: "Designer",
    urgency: "New",
    postedAt: "2 hours ago"
  }
];

const MOCK_AVAILABLE_PROJECTS = [
  {
    id: 'p1',
    title: "Full Stack Web Application",
    client: "StartupXYZ",
    avatar: "TC",
    rating: 4.9,
    description: "Build a complete web application with authentication, dashboard, and API integration. Must be proficient in modern frontend frameworks.",
    budget: "$12,000",
    budgetType: "Fixed Price",
    timeline: "3 months",
    proposals: 8,
    skills: ["React", "Node.js", "PostgreSQL"],
    category: "Designer",
    urgency: "Urgent",
    postedAt: "3 hours ago"
  },
  {
    id: 'p2',
    title: "Landing Page Design & Development",
    client: "Marketing Agency",
    avatar: "MA",
    rating: 4.7,
    description: "High-converting landing page for a new SaaS product. Design assets provided in Figma.",
    budget: "$2,500",
    budgetType: "Fixed Price",
    timeline: "2 weeks",
    proposals: 12,
    skills: ["Figma", "Tailwind CSS", "React"],
    category: "Designer",
    urgency: "Popular",
    postedAt: "6 hours ago"
  },
  {
    id: 'p3',
    title: "Wedding Choreography - 5 Songs",
    client: "The Kapoor Family",
    avatar: "KF",
    rating: 4.5,
    description: "Need a choreographer for a 3-day wedding event. Styles: Bollywood, Hip Hop.",
    budget: "$1,500",
    budgetType: "Fixed Price",
    timeline: "1 month",
    proposals: 5,
    skills: ["Bollywood", "Hip Hop", "Choreography"],
    category: "Dance",
    urgency: "New",
    postedAt: "1 day ago"
  }
];

export default function OpportunitiesPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('hire-requests');
  const [sidebarActive, setSidebarActive] = useState('opportunities');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isProposalModalOpen, setIsProposalModalOpen] = useState(false);
  
  // Use user category for filtering mock data
  const userCategory = useMemo(() => {
    return localStorage.getItem('gb_artist_category') || 'Designer';
  }, []);

  // State for mock interaction
  const [hireRequests, setHireRequests] = useState(() => {
    return MOCK_HIRE_REQUESTS.filter(r => r.category.toLowerCase().includes(userCategory.toLowerCase()) || 
                                         userCategory.toLowerCase().includes(r.category.toLowerCase()));
  });
  const [availableProjects, setAvailableProjects] = useState(() => {
    return MOCK_AVAILABLE_PROJECTS.filter(p => p.category.toLowerCase().includes(userCategory.toLowerCase()) || 
                                              userCategory.toLowerCase().includes(p.category.toLowerCase()));
  });

  const calculateMatchScore = (projectSkills, userSkills) => {
    const matches = projectSkills.filter(skill => userSkills.includes(skill)).length;
    const score = Math.round((matches / projectSkills.length) * 100);
    return Math.max(score, 60); // Minimum 60% for category matches
  };

  const filteredProjects = useMemo(() => {
    const list = activeTab === 'hire-requests' ? hireRequests : availableProjects;
    
    return list
      .map(p => ({
        ...p,
        matchScore: calculateMatchScore(p.skills, MOCK_USER.skills)
      }))
      .filter(p => {
        const matchesSearch = p.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                             p.client.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesSearch;
      })
      .sort((a, b) => b.matchScore - a.matchScore);
  }, [activeTab, searchQuery, hireRequests, availableProjects]);

  const recommendedProjects = useMemo(() => {
    return availableProjects
      .map(p => ({
        ...p,
        matchScore: calculateMatchScore(p.skills, MOCK_USER.skills)
      }))
      .filter(p => p.category === MOCK_USER.category)
      .sort((a, b) => b.matchScore - a.matchScore)
      .slice(0, 2);
  }, [availableProjects]);

  const handleDecline = (id) => {
    setHireRequests(prev => prev.filter(r => r.id !== id));
  };

  const handleOpenProposal = (project) => {
    setSelectedProject(project);
    setIsProposalModalOpen(true);
  };

  return (
    <div className="db-layout">
      <DashboardHeader />
      <div className="db-shell">
        <DashboardSidebar active={sidebarActive} onSelect={setSidebarActive} />
        <main className="db-main opportunities-page">
          <div className="opps-header">
            <h2>Opportunities</h2>
            <p>Manage hire requests and browse available projects</p>
          </div>

          <div className="opps-tabs">
            <button 
              className={`opps-tab ${activeTab === 'hire-requests' ? 'active' : ''}`}
              onClick={() => setActiveTab('hire-requests')}
            >
              Hire Requests <span className="tab-badge">{hireRequests.length}</span>
            </button>
            <button 
              className={`opps-tab ${activeTab === 'available-projects' ? 'active' : ''}`}
              onClick={() => setActiveTab('available-projects')}
            >
              Available Projects
            </button>
          </div>

          <div className="opps-controls">
            <div className="opps-search">
              <span className="search-icon">🔍</span>
              <input 
                type="text" 
                placeholder="Search projects..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button className="filter-toggle" onClick={() => setShowFilters(!showFilters)}>
              <span className="filter-icon">⚙️</span> Filters
            </button>
          </div>

          {showFilters && <FilterPanel onClose={() => setShowFilters(false)} />}

          {activeTab === 'available-projects' && searchQuery === '' && (
            <RecommendedProjects projects={recommendedProjects} onApply={handleOpenProposal} />
          )}

          <div className="opps-list">
            {filteredProjects.length > 0 ? (
              filteredProjects.map(item => (
                activeTab === 'hire-requests' ? (
                  <HireRequestCard 
                    key={item.id} 
                    data={item} 
                    onDecline={() => handleDecline(item.id)} 
                  />
                ) : (
                  <ProjectCard 
                    key={item.id} 
                    data={item} 
                    onApply={() => handleOpenProposal(item)} 
                  />
                )
              ))
            ) : (
              <EmptyStateOpportunities onRefresh={() => setSearchQuery('')} />
            )}
          </div>
        </main>
      </div>

      {isProposalModalOpen && (
        <ProposalModal 
          project={selectedProject} 
          onClose={() => setIsProposalModalOpen(false)}
          onSubmit={(proposal) => {
            console.log("Proposal submitted:", proposal);
            setIsProposalModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
