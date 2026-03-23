import Navbar from "./components/Navbar.jsx";
import Hero from "./components/Hero.jsx";
import AuthSignup from "./components/AuthSignup.jsx";
import AuthLogin from "./components/AuthLogin.jsx";
import ForgotPassword from "./components/ForgotPassword.jsx";
import ClientProfileSetup from "./components/ClientProfileSetup.jsx";
import FreelancerProfileSetup from "./components/FreelancerProfileSetup.jsx";
import Onboarding from "./components/Onboarding.jsx";
import ChoosePath from "./components/ChoosePath.jsx";
import PostProject from "./components/PostProject.jsx";
import BrowseArtists from "./components/BrowseArtists.jsx";
import Messages from "./components/Messages.jsx";
import ClientProfile from "./components/ClientProfile.jsx";
import ArtistProfile from "./components/ArtistProfile.jsx";
import PaymentPage from "./components/PaymentPage.jsx";
import GoogleAuthCallback from "./components/GoogleAuthCallback.jsx";
import "./App.css";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext.jsx";
import PublicRoute from "./components/routes/PublicRoute.jsx";
import ProtectedClientRoute from "./components/routes/ProtectedClientRoute.jsx";
import ProtectedFreelancerRoute from "./components/routes/ProtectedFreelancerRoute.jsx";
import FreelancerProfileStep1 from "./pages/FreelancerProfileStep1.jsx";
import FreelancerProfileStep2 from "./pages/FreelancerProfileStep2.jsx";
import ArtistDashboard from "./pages/ArtistDashboard.jsx";
import FreelancerProfilePage from "./pages/FreelancerProfilePage.jsx";
import FreelancerPortfolioPage from "./pages/FreelancerPortfolioPage.jsx";
import OpportunitiesPage from "./pages/OpportunitiesPage.jsx";
import GigActivityPage from "./pages/GigActivityPage.jsx";
import MessagesPage from "./pages/MessagesPage.jsx";
import ClientMessagesPage from "./pages/ClientMessagesPage.jsx";
import DashboardHeader from "./components/DashboardHeader.jsx";
import DashboardSidebar from "./components/DashboardSidebar.jsx";
import DashboardPlaceholder from "./components/DashboardPlaceholder.jsx";
import NotificationsPage from "./pages/NotificationsPage.jsx";
import FavoritesPage from "./pages/FavoritesPage.jsx";
import VerificationPage from "./pages/VerificationPage.jsx";
import SubscriptionPage from "./pages/SubscriptionPage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";
import MyProjects from "./pages/MyProjects.jsx";
import ViewApplicants from "./pages/ViewApplicants.jsx";

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

const AppContent = () => {
  const location = useLocation();
  const isArtistDashboard = 
    location.pathname.startsWith("/artist/") || 
    location.pathname === "/dashboard";

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<PublicRoute><><Hero /><StatsStrip /></></PublicRoute>} />
        <Route path="/signup/:role" element={<PublicRoute><AuthSignup /></PublicRoute>} />
        <Route path="/login/:role" element={<PublicRoute><AuthLogin /></PublicRoute>} />
        <Route path="/forgot-password/:role" element={<ForgotPassword />} />
        <Route path="/auth/callback" element={<GoogleAuthCallback />} />

        <Route path="/client/profile-setup" element={
          <ProtectedClientRoute requireCompleted={false}><ClientProfileSetup /></ProtectedClientRoute>
        } />
        <Route path="/freelancer/profile-setup" element={
          <ProtectedClientRoute requireCompleted={false}><FreelancerProfileSetup /></ProtectedClientRoute>
        } />
        <Route path="/freelancer/create-profile/step-1" element={
          <ProtectedFreelancerRoute requireCompleted={false}><FreelancerProfileStep1 /></ProtectedFreelancerRoute>
        } />
        <Route path="/freelancer/create-profile/step-2" element={
          <ProtectedFreelancerRoute requireCompleted={false}><FreelancerProfileStep2 /></ProtectedFreelancerRoute>
        } />

        <Route path="/onboarding" element={
          <ProtectedClientRoute><Onboarding /></ProtectedClientRoute>
        } />
        <Route path="/dashboard" element={
          <Navigate to="/artist/dashboard" replace />
        } />
        <Route path="/artist/dashboard" element={
          <ProtectedFreelancerRoute><ArtistDashboard /></ProtectedFreelancerRoute>
        } />
        <Route path="/artist/profile" element={
          <ProtectedFreelancerRoute><FreelancerProfilePage /></ProtectedFreelancerRoute>
        } />
        <Route path="/artist/portfolio" element={
          <ProtectedFreelancerRoute><FreelancerPortfolioPage /></ProtectedFreelancerRoute>
        } />
        <Route path="/artist/opportunities" element={
          <ProtectedFreelancerRoute><OpportunitiesPage /></ProtectedFreelancerRoute>
        } />
        <Route path="/artist/projects" element={
          <ProtectedFreelancerRoute><GigActivityPage /></ProtectedFreelancerRoute>
        } />
        <Route path="/artist/messages" element={
          <ProtectedFreelancerRoute><MessagesPage /></ProtectedFreelancerRoute>
        } />
        <Route path="/artist/notifications" element={
          <ProtectedFreelancerRoute><NotificationsPage /></ProtectedFreelancerRoute>
        } />
        <Route path="/artist/verification" element={
          <ProtectedFreelancerRoute><VerificationPage /></ProtectedFreelancerRoute>
        } />
        <Route path="/artist/subscription" element={
          <ProtectedFreelancerRoute><SubscriptionPage /></ProtectedFreelancerRoute>
        } />
        <Route path="/artist/settings" element={
          <ProtectedFreelancerRoute><SettingsPage /></ProtectedFreelancerRoute>
        } />
        <Route path="/choose-path" element={
          <ProtectedClientRoute><ChoosePath /></ProtectedClientRoute>
        } />
        <Route path="/client/post-project" element={
          <ProtectedClientRoute><PostProject /></ProtectedClientRoute>
        } />
        <Route path="/post-project" element={<Navigate to="/client/post-project" replace />} />
        <Route path="/browse-artists" element={
          <ProtectedClientRoute><BrowseArtists /></ProtectedClientRoute>
        } />
        <Route path="/browse" element={<Navigate to="/browse-artists" replace />} />
        <Route path="/messages" element={
          <ProtectedClientRoute><ClientMessagesPage /></ProtectedClientRoute>
        } />
        <Route path="/notifications" element={
          <ProtectedClientRoute><NotificationsPage /></ProtectedClientRoute>
        } />
        <Route path="/favorites" element={
          <ProtectedClientRoute><FavoritesPage /></ProtectedClientRoute>
        } />
        <Route path="/profile" element={
          <ProtectedClientRoute><ClientProfile /></ProtectedClientRoute>
        } />
        <Route path="/artist/:id" element={
          <ProtectedClientRoute><ArtistProfile /></ProtectedClientRoute>
        } />
        <Route path="/payment" element={
          <ProtectedClientRoute><PaymentPage /></ProtectedClientRoute>
        } />
        <Route path="/my-projects" element={
          <ProtectedClientRoute><MyProjects /></ProtectedClientRoute>
        } />
        <Route path="/project/:id/applicants" element={
          <ProtectedClientRoute><ViewApplicants /></ProtectedClientRoute>
        } />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
