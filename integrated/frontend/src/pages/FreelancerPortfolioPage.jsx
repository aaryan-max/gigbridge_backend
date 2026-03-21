import React, { useState } from 'react';
import DashboardHeader from '../components/DashboardHeader';
import DashboardSidebar from '../components/DashboardSidebar';
import PortfolioHeader from '../components/PortfolioHeader';
import PortfolioGrid from '../components/PortfolioGrid';
import EmptyPortfolioState from '../components/EmptyPortfolioState';
import AddProjectModal from '../components/AddProjectModal';
import './dashboard.css';
import './portfolio.css';

const MOCK_PROJECTS = [
  {
    id: 1,
    title: "Modern E-commerce Website",
    description: "A fully responsive e-commerce platform with advanced filtering and checkout.",
    category: "Designer",
    tags: ["React", "TypeScript", "Tailwind CSS"],
    image: "https://images.unsplash.com/photo-1557821552-17105176677c?w=500"
  },
  {
    id: 2,
    title: "Mobile Banking App",
    description: "Clean and intuitive mobile banking interface with advanced security features.",
    category: "Designer",
    tags: ["React Native", "UI/UX", "Figma"],
    image: "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=500"
  },
  {
    id: 3,
    title: "Analytics Dashboard",
    description: "Real-time analytics dashboard with interactive charts and data visualization.",
    category: "Designer",
    tags: ["Vue.js", "D3.js", "Node.js"],
    image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=500"
  }
];

export default function FreelancerPortfolioPage() {
  const [active, setActive] = useState("portfolio");
  const [projects, setProjects] = useState(MOCK_PROJECTS);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleAddProject = (newProject) => {
    setProjects(prev => [{ ...newProject, id: Date.now() }, ...prev]);
    setIsModalOpen(false);
  };

  const handleDeleteProject = (id) => {
    setProjects(prev => prev.filter(p => p.id !== id));
  };

  return (
    <div className="db-layout">
      <DashboardHeader />
      <div className="db-shell">
        <DashboardSidebar active={active} onSelect={setActive} />
        <main className="db-main portfolio-page">
          <PortfolioHeader onAddClick={() => setIsModalOpen(true)} />
          
          {projects.length > 0 ? (
            <PortfolioGrid 
              projects={projects} 
              onDelete={handleDeleteProject}
            />
          ) : (
            <EmptyPortfolioState onAddClick={() => setIsModalOpen(true)} />
          )}
        </main>
      </div>

      {isModalOpen && (
        <AddProjectModal 
          onClose={() => setIsModalOpen(false)}
          onSave={handleAddProject}
        />
      )}
    </div>
  );
}
