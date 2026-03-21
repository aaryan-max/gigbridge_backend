import { createContext, useContext, useEffect, useMemo, useState } from "react";

const AuthContext = createContext(null);

const AUTH_KEY = "gb_auth";
const USER_DATA_KEY = "gb_user_data";
const PROFILE_DONE_KEY = "gb_profile_done";

function loadFromStorage(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [userData, setUserData] = useState(() => loadFromStorage(USER_DATA_KEY));
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => typeof window !== "undefined" && localStorage.getItem(AUTH_KEY) === "1"
  );
  const [profileCompleted, setProfileCompleted] = useState(
    () => typeof window !== "undefined" && localStorage.getItem(PROFILE_DONE_KEY) === "1"
  );

  useEffect(() => {
    const onStorage = () => {
      setIsAuthenticated(localStorage.getItem(AUTH_KEY) === "1");
      setProfileCompleted(localStorage.getItem(PROFILE_DONE_KEY) === "1");
      setUserData(loadFromStorage(USER_DATA_KEY));
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const login = (data) => {
    const userInfo = {
      email: data.email,
      role: data.role,
      name: data.name || "",
      id: data.client_id || data.freelancer_id || null,
    };
    localStorage.setItem(AUTH_KEY, "1");
    localStorage.setItem(USER_DATA_KEY, JSON.stringify(userInfo));
    if (data.profile_completed) {
      localStorage.setItem(PROFILE_DONE_KEY, "1");
      setProfileCompleted(true);
    }
    setIsAuthenticated(true);
    setUserData(userInfo);
  };

  const logout = () => {
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(USER_DATA_KEY);
    localStorage.removeItem(PROFILE_DONE_KEY);
    setIsAuthenticated(false);
    setUserData(null);
    setProfileCompleted(false);
  };

  const markProfileCompleted = () => {
    localStorage.setItem(PROFILE_DONE_KEY, "1");
    setProfileCompleted(true);
  };

  const role = userData?.role || null;

  const value = useMemo(
    () => ({
      user: {
        isAuthenticated,
        role,
        profileCompleted,
        email: userData?.email || null,
        name: userData?.name || null,
        id: userData?.id || null,
      },
      login,
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
