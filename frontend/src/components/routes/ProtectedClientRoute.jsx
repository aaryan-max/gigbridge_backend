import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext.jsx";

export default function ProtectedClientRoute({ children, requireCompleted = true }) {
  const { user } = useAuth();
  const loc = useLocation();
  if (!user.isAuthenticated) {
    return <Navigate to="/login/client" state={{ from: loc }} replace />;
  }
  if (requireCompleted && !user.profileCompleted) {
    return <Navigate to="/client/profile-setup" replace />;
  }
  if (!requireCompleted && user.profileCompleted) {
    return <Navigate to="/onboarding" replace />;
  }
  return children;
}
