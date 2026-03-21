import { Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext.jsx";

export default function PublicRoute({ children }) {
  const { user } = useAuth();

  if (!user.isAuthenticated) {
    return children;
  }

  if (user.role === "client") {
    if (user.profileCompleted) {
      return <Navigate to="/onboarding" replace />;
    }
    return <Navigate to="/client/profile-setup" replace />;
  }

  if (user.role === "freelancer") {
    if (user.profileCompleted) {
      return <Navigate to="/onboarding" replace />;
    }
    return <Navigate to="/freelancer/profile-setup" replace />;
  }

  return <Navigate to="/onboarding" replace />;
}
