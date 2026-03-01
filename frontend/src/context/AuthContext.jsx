import { createContext, useContext, useEffect, useMemo, useState } from "react";

const AuthContext = createContext(null);

const CLIENT_AUTH_KEY = "client_auth";
const CLIENT_DONE_KEY = "client_profile_done";

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(
    typeof window !== "undefined" && localStorage.getItem(CLIENT_AUTH_KEY) === "1"
  );
  const [profileCompleted, setProfileCompleted] = useState(
    typeof window !== "undefined" && localStorage.getItem(CLIENT_DONE_KEY) === "1"
  );
  const role = "client";

  useEffect(() => {
    const onStorage = () => {
      setIsAuthenticated(localStorage.getItem(CLIENT_AUTH_KEY) === "1");
      setProfileCompleted(localStorage.getItem(CLIENT_DONE_KEY) === "1");
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const loginClient = () => {
    localStorage.setItem(CLIENT_AUTH_KEY, "1");
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem(CLIENT_AUTH_KEY);
    setIsAuthenticated(false);
  };

  const markProfileCompleted = () => {
    localStorage.setItem(CLIENT_DONE_KEY, "1");
    setProfileCompleted(true);
  };

  const value = useMemo(
    () => ({
      user: { isAuthenticated, role, profileCompleted },
      loginClient,
      logout,
      markProfileCompleted,
    }),
    [isAuthenticated, profileCompleted]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
