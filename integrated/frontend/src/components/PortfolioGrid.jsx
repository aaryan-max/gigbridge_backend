import React from 'react';
import PortfolioCard from './PortfolioCard';

export default function PortfolioGrid({ projects, onDelete }) {
  return (
    <div className="portfolio-grid-layout">
      {projects.map(project => (
        <PortfolioCard 
          key={project.id} 
          project={project} 
          onDelete={() => onDelete(project.id)}
        />
      ))}
    </div>
  );
}
