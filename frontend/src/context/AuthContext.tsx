import { createContext, useContext, useEffect, useState } from "react";
import { getCurrentUser, getToken, removeToken, saveToken } from "../services/authApi";
import type { AuthUser } from "../types/auth";

interface AuthContextValue {
    // Current logged-in user. Null means not logged in.
    user: AuthUser | null;

    // True while checking localStorage token with the backend.
    isLoading: boolean;

    // Called after successful login/register to update the whole app.
    login: (token: string) => Promise<void>;

    // Called when user clicks logout.
    logout: () => void;
}

// Context is initially undefined so we can catch incorrect usage.
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    // Shared user state for Navbar, LoginPage, RegistrationPage, etc.
    const [user, setUser] = useState<AuthUser | null>(null);

    // Loading state prevents navbar from briefly showing wrong auth UI.
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        async function loadUserFromSavedToken() {
        const token = getToken();

        // If no token exists, user is not logged in.
        if (token === null) {
            setUser(null);
            setIsLoading(false);
            return;
        }

        try {
            // Checks whether the saved token is still valid.
            const currentUser = await getCurrentUser();
            setUser(currentUser);
        } catch {
            // If token is invalid or expired, remove it.
            removeToken();
            setUser(null);
        } finally {
            setIsLoading(false);
        }
        }

        loadUserFromSavedToken();
  }, []);

    async function login(token: string) {
        // Save token first so getCurrentUser() can send it to /auth/me.
        saveToken(token);

        // Fetch user details and update the shared auth state.
        const currentUser = await getCurrentUser();
        setUser(currentUser);
    }

    function logout() {
        removeToken();
        setUser(null);
    }

    return (
        <AuthContext.Provider value={{ user, isLoading, login, logout }}>
        {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    // Custom hook so components can easily read auth state.
    const context = useContext(AuthContext);

    if (context === undefined) {
        throw new Error("useAuth must be used inside AuthProvider");
    }

    return context;
}