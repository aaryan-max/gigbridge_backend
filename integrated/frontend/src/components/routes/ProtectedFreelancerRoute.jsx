import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext.jsx";

export default function ProtectedFreelancerRoute({ children, requireCompleted = true }) {
  const { user } = useAuth();
  const loc = useLocation();

  if (!user.isAuthenticated) {
    return <Navigate to="/login/freelancer" state={{ from: loc }} replace />;
  }

  if (user.role !== "freelancer") {
    return <Navigate to="/" replace />;
  }

  if (requireCompleted && !user.profileCompleted) {
    return <Navigate to="/freelancer/create-profile/step-1" replace />;
  }

  if (!requireCompleted && user.profileCompleted) {
    return <Navigate to="/artist/dashboard" replace />;
  }

  return children;
}
