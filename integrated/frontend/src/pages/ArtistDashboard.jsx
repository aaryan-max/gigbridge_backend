import { useEffect, useMemo, useState } from "react";
import DashboardHeader from "../components/DashboardHeader.jsx";
import DashboardSidebar from "../components/DashboardSidebar.jsx";
import StatsCard from "../components/StatsCard.jsx";
import ProgressCard from "../components/ProgressCard.jsx";
import ActivityFeed from "../components/ActivityFeed.jsx";
import { artistService } from "../services/artistService.js";
import { useAuth } from "../context/AuthContext.jsx";
import "./dashboard.css";

const VALID_CATEGORIES = [
  "Photographer","Videographer","DJ","Singer","Dancer","Anchor","Makeup Artist","Mehendi Artist","Decorator","Wedding Planner","Choreographer","Band / Live Music","Magician / Entertainer","Artist","Event Organizer",
];

export default function ArtistDashboard() {
  const { user } = useAuth();
  const [active, setActive] = useState("dashboard");
  const [search, setSearch] = useState("");
  const [dash, setDash] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [activity, setActivity] = useState([]);

  useEffect(() => {
    if (!user?.id) return;
    let mounted = true;
    (async () => {
      const d = await artistService.getDashboard(user.id);
      const b = await artistService.getBookings(user.id);
      const a = await artistService.getActivity(user.id);
      if (!mounted) return;
      setDash(d);
      setBookings(b.bookings || []);
      setActivity(a.items || []);
    })();
    return () => { mounted = false; };
  }, [user?.id]);

  const welcomeName = useMemo(() => dash?.artist?.name || "Artist", [dash]);
  const progressPct = useMemo(() => {
    const catScore = VALID_CATEGORIES.includes(dash?.artist?.category || "") ? 0.2 : 0.05;
    const base = dash?.progress?.completeness ?? 0.5;
    return Math.round((base + catScore) * 100);
  }, [dash]);

  const stats = dash?.stats || { earnings: 0, bookings: 0, requests: 0, successRate: 0, growthText: {} };

  const filteredBookings = useMemo(() => {
    if (!search) return bookings;
    const s = search.toLowerCase();
    return bookings.filter(b => (b.event || "").toLowerCase().includes(s) || (b.client || "").toLowerCase().includes(s));
  }, [bookings, search]);

  return (
    <>
      <DashboardHeader onSearch={setSearch} />
      <div className="db-shell">
        <DashboardSidebar active={active} onSelect={setActive} />
        <main className="db-main">
          <div className="db-top-row">
            <div className="db-welcome">
              <h2>Welcome back, {welcomeName} 🎤</h2>
              <p>Here’s what’s happening with your artist bookings today.</p>
            </div>
          </div>

          <ProgressCard
            title="Complete Your Artist Profile"
            desc="Complete your profile to get more bookings"
            percent={progressPct}
          />

          <section className="db-cards">
            <StatsCard icon="💸" color="#2563eb" title="Total Earnings" value={`₹${stats.earnings?.toLocaleString?.() || stats.earnings}`} subtext={stats.growthText?.earnings} />
            <StatsCard icon="📅" color="#06b6d4" title="Upcoming Bookings" value={stats.bookings} subtext={stats.growthText?.bookings} />
            <StatsCard icon="📩" color="#f59e0b" title="Pending Event Requests" value={stats.requests} subtext={stats.growthText?.requests} />
            <StatsCard icon="✅" color="#10b981" title="Success Rate" value={`${stats.successRate}%`} subtext={stats.growthText?.successRate} />
          </section>

          <section className="db-section">
            <div className="db-section-title">Upcoming Performances</div>
            {filteredBookings.map((b) => (
              <div key={b.id} className="db-booking">
                <div className="db-booking-info">
                  <div className="db-booking-title">{b.event}</div>
                  <div className="db-booking-sub">{b.client} • {b.date}</div>
                </div>
                <div style={{ minWidth: 180 }}>
                  <div className="db-booking-val">₹{b.value?.toLocaleString?.() || b.value}</div>
                  <div className="db-booking-bar"><div className="db-booking-fill" style={{ width: `${b.progress}%` }} /></div>
                </div>
              </div>
            ))}
          </section>

          <ActivityFeed items={activity} />

        </main>
      </div>
    </>
  );
}
