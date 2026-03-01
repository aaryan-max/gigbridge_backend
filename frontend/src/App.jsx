import Navbar from "./components/Navbar.jsx";
import Hero from "./components/Hero.jsx";
import AuthSignup from "./components/AuthSignup.jsx";
import AuthLogin from "./components/AuthLogin.jsx";
import ClientProfileSetup from "./components/ClientProfileSetup.jsx";
import Onboarding from "./components/Onboarding.jsx";
import ChoosePath from "./components/ChoosePath.jsx";
import PostProject from "./components/PostProject.jsx";
import BrowseArtists from "./components/BrowseArtists.jsx";
import Messages from "./components/Messages.jsx";
import ClientProfile from "./components/ClientProfile.jsx";
import ArtistProfile from "./components/ArtistProfile.jsx";
import "./App.css";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext.jsx";
import PublicRoute from "./components/routes/PublicRoute.jsx";
import ProtectedClientRoute from "./components/routes/ProtectedClientRoute.jsx";

export default function App() {
  const ClientDashboard = () => <div style={{ padding: 24 }}>Client Dashboard</div>;
  const RequireClientProfile = ({ children }) => {
    const done = localStorage.getItem("client_profile_done") === "1";
    if (!done) return <Navigate to="/client/profile-setup" replace />;
    return children;
  };
  const StatsStrip = () => (
    <section className="stats">
      <div className="stats-inner">
        <div className="stat-card">
          <div className="stat-value">10K+</div>
          <div className="stat-label">Active Artists</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">50K+</div>
          <div className="stat-label">Projects Completed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">4.9/5</div>
          <div className="stat-label">Average Rating</div>
        </div>
      </div>
    </section>
  );
  return (
    <AuthProvider>
      <Navbar />
      <Routes>
        <Route
          path="/"
          element={
            <PublicRoute>
              <>
                <Hero />
                <StatsStrip />
              </>
            </PublicRoute>
          }
        />
        <Route
          path="/signup/:role"
          element={
            <PublicRoute>
              <AuthSignup />
            </PublicRoute>
          }
        />
        <Route
          path="/login/:role"
          element={
            <PublicRoute>
              <AuthLogin />
            </PublicRoute>
          }
        />
        <Route
          path="/client/profile-setup"
          element={
            <ProtectedClientRoute requireCompleted={false}>
              <ClientProfileSetup />
            </ProtectedClientRoute>
          }
        />
        <Route
          path="/onboarding"
          element={
            <ProtectedClientRoute>
              <Onboarding />
            </ProtectedClientRoute>
          }
        />
        <Route
          path="/choose-path"
          element={
            <ProtectedClientRoute>
              <ChoosePath />
            </ProtectedClientRoute>
          }
        />
        <Route
          path="/client/post-project"
          element={
            <ProtectedClientRoute>
              <PostProject />
            </ProtectedClientRoute>
          }
        />
        <Route path="/post-project" element={<Navigate to="/client/post-project" replace />} />
        <Route
          path="/browse-artists"
          element={
            <ProtectedClientRoute>
              <BrowseArtists />
            </ProtectedClientRoute>
          }
        />
        <Route path="/browse" element={<Navigate to="/browse-artists" replace />} />
        <Route
          path="/messages"
          element={
            <ProtectedClientRoute>
              <Messages />
            </ProtectedClientRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedClientRoute>
              <ClientProfile />
            </ProtectedClientRoute>
          }
        />
        <Route
          path="/artist/:id"
          element={
            <ProtectedClientRoute>
              <ArtistProfile />
            </ProtectedClientRoute>
          }
        />
        <Route
          path="/dashboard/client"
          element={
            <RequireClientProfile>
              <ClientDashboard />
            </RequireClientProfile>
          }
        />
      </Routes>
    </AuthProvider>
  );
}
