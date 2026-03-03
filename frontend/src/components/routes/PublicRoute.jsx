import { Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext.jsx";

export default function PublicRoute({ children }) {
  const { user } = useAuth();
  if (user.isAuthenticated && user.profileCompleted) {
    return <Navigate to="/onboarding" replace />;
  }
  if (user.isAuthenticated && !user.profileCompleted) {
    return <Navigate to="/client/profile-setup" replace />;
  }
  return children;
}
