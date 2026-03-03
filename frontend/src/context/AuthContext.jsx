import { createContext, useContext, useEffect, useMemo, useState } from "react";

const AuthContext = createContext(null);

const CLIENT_AUTH_KEY = "client_auth";
const CLIENT_DONE_KEY = "client_profile_done";
const USER_DATA_KEY = "user_data";

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(
    typeof window !== "undefined" && localStorage.getItem(CLIENT_AUTH_KEY) === "1"
  );
  const [profileCompleted, setProfileCompleted] = useState(
    typeof window !== "undefined" && localStorage.getItem(CLIENT_DONE_KEY) === "1"
  );
  const [userData, setUserData] = useState(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(USER_DATA_KEY);
      return stored ? JSON.parse(stored) : null;
    }
    return null;
  });
  const role = userData?.role || "client";

  useEffect(() => {
    const onStorage = () => {
      setIsAuthenticated(localStorage.getItem(CLIENT_AUTH_KEY) === "1");
      setProfileCompleted(localStorage.getItem(CLIENT_DONE_KEY) === "1");
      const stored = localStorage.getItem(USER_DATA_KEY);
      setUserData(stored ? JSON.parse(stored) : null);
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const loginClient = (data) => {
    localStorage.setItem(CLIENT_AUTH_KEY, "1");
    localStorage.setItem(USER_DATA_KEY, JSON.stringify(data));
    setIsAuthenticated(true);
    setUserData(data);
  };

  const logout = () => {
    localStorage.removeItem(CLIENT_AUTH_KEY);
    localStorage.removeItem(USER_DATA_KEY);
    localStorage.removeItem(CLIENT_DONE_KEY);
    setIsAuthenticated(false);
    setUserData(null);
    setProfileCompleted(false);
  };

  const markProfileCompleted = () => {
    localStorage.setItem(CLIENT_DONE_KEY, "1");
    setProfileCompleted(true);
  };

  const value = useMemo(
    () => ({
      user: { isAuthenticated, role, profileCompleted, ...userData },
      loginClient,
      logout,
      markProfileCompleted,
    }),
    [isAuthenticated, profileCompleted, userData, role]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
