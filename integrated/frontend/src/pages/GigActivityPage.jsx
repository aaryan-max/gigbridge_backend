import React, { useState, useMemo } from 'react';
import DashboardHeader from '../components/DashboardHeader';
import DashboardSidebar from '../components/DashboardSidebar';
import GigActivityCard from '../components/GigActivityCard';
import WeeklySummaryCard from '../components/WeeklySummaryCard';
import MonthlyStatsSection from '../components/MonthlyStatsSection';
import AddGigModal from '../components/AddGigModal';
import EmptyStateCard from '../components/EmptyStateCard';
import { useAuth } from '../context/AuthContext';
import './dashboard.css';
import './gigActivity.css';

const MOCK_GIGS = [
  {
    id: 1,
    title: "Wedding Dance Performance",
    description: "Choreographed and performed sangeet routine for 20 minutes.",
    category: "Dance",
    date: "12 Mar 2026",
    hours: 4,
    status: "Completed"
  },
  {
    id: 2,
    title: "Corporate Event Photography",
    description: "Covered annual awards ceremony and edited 50 high-res photos.",
    category: "Photography",
    date: "10 Mar 2026",
    hours: 6,
    status: "Completed"
  },
  {
    id: 3,
    title: "Live Music Show",
    description: "Performed 2-hour set with the band at City Music Festival.",
    category: "Music Band",
    date: "15 Mar 2026",
    hours: 5,
    status: "Upcoming"
  },
  {
    id: 4,
    title: "DJ Night - Club Fusion",
    description: "4-hour DJ set for weekend party crowd.",
    category: "DJ Performance",
    date: "14 Mar 2026",
    hours: 4,
    status: "Ongoing"
  }
];

export default function GigActivityPage() {
  const { user } = useAuth();
  const [active, setActive] = useState("projects");
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Use user category for filtering mock data
  const userCategory = useMemo(() => {
    return localStorage.getItem('gb_artist_category') || 'Dance';
  }, []);

  const INITIAL_GIGS = useMemo(() => {
    const all = [
      { id: 1, title: "Wedding Dance Performance", description: "Choreographed and performed sangeet routine.", category: "Dance", date: "12 Mar 2026", hours: 4, status: "Completed" },
      { id: 2, title: "Corporate Event Photography", description: "Covered annual awards ceremony.", category: "Photography", date: "10 Mar 2026", hours: 6, status: "Completed" },
      { id: 3, title: "Live Music Show", description: "Performed 2-hour set with the band.", category: "Music Band", date: "15 Mar 2026", hours: 5, status: "Upcoming" },
      { id: 4, title: "DJ Night - Club Fusion", description: "4-hour DJ set for weekend party crowd.", category: "DJ Performance", date: "14 Mar 2026", hours: 4, status: "Ongoing" },
      { id: 5, title: "Product Shoot - New Collection", description: "Studio shoot for apparel brand.", category: "Photography", date: "08 Mar 2026", hours: 8, status: "Completed" },
      { id: 6, title: "Sangeet Choreography", description: "Taught dance to 10 family members.", category: "Dance", date: "05 Mar 2026", hours: 12, status: "Completed" },
      { id: 7, title: "Birthday Party DJ", description: "Handled music for private birthday.", category: "DJ Performance", date: "02 Mar 2026", hours: 3, status: "Completed" }
    ];
    // Only return gigs matching user category
    return all.filter(g => g.category.toLowerCase().includes(userCategory.toLowerCase()) || 
                          userCategory.toLowerCase().includes(g.category.toLowerCase()));
  }, [userCategory]);

  const [gigs, setGigs] = useState(INITIAL_GIGS);

  const weeklySummary = useMemo(() => {
    const totalGigs = gigs.filter(g => g.status === 'Completed' || g.status === 'Ongoing').length;
    const totalHours = gigs.reduce((acc, curr) => acc + curr.hours, 0);
    const categoryBreakdown = gigs.reduce((acc, curr) => {
      acc[curr.category] = (acc[curr.category] || 0) + 1;
      return acc;
    }, {});
    return { totalGigs, totalHours, categoryBreakdown };
  }, [gigs]);

  const monthlyStats = {
    totalGigs: 9,
    performanceHours: 56,
    eventsWorked: 7,
    estimatedEarnings: 45000
  };

  const handleAddGig = (newGig) => {
    setGigs(prev => [{ ...newGig, id: Date.now() }, ...prev]);
    setIsModalOpen(false);
  };

  return (
    <div className="db-layout">
      <DashboardHeader />
      <div className="db-shell">
        <DashboardSidebar active={active} onSelect={setActive} />
        <main className="db-main gig-activity-page">
          <div className="gig-activity-grid">
            {/* Left Section: Activity Logs */}
            <div className="gig-activity-logs">
              <div className="section-header">
                <h3>Recent Gig Activity</h3>
                <button className="add-entry-btn" onClick={() => setIsModalOpen(true)}>
                  <span className="plus-icon">+</span> Add Gig Activity
                </button>
              </div>

              <div className="gig-cards-container">
                {gigs.length > 0 ? (
                  gigs.map(gig => (
                    <GigActivityCard key={gig.id} gig={gig} />
                  ))
                ) : (
                  <EmptyStateCard onAdd={() => setIsModalOpen(true)} />
                )}
              </div>
            </div>

            {/* Right Section: Weekly Summary */}
            <div className="gig-activity-summary">
              <WeeklySummaryCard summary={weeklySummary} />
            </div>
          </div>

          {/* Bottom Section: Monthly Stats */}
          <MonthlyStatsSection stats={monthlyStats} />
        </main>
      </div>

      {isModalOpen && (
        <AddGigModal 
          onClose={() => setIsModalOpen(false)}
          onSave={handleAddGig}
        />
      )}
    </div>
  );
}
