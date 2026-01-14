/**
 * Authentication Context for Escrow Platform
 * Manages user authentication state across the app
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, TokenManager } from '../lib/api';

// User type
interface User {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    full_name: string;
    role: string;
    status: string;
    kyc_status: string;
    email_verified: boolean;
    two_factor_enabled: boolean;
    can_transact: boolean;
    effective_plan: {
        name: string;
        fee_percent: string;
        sla_hours: number;
        max_transaction_limit?: string;
        features: {
            api_access: boolean;
            dedicated_support: boolean;
            white_labeling: boolean;
        };
    };
}

// Auth context type
interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (data: RegisterData) => Promise<void>;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
}

interface RegisterData {
    email: string;
    password: string;
    password_confirm: string;
    first_name: string;
    last_name: string;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check for existing session on mount
    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            if (TokenManager.hasTokens()) {
                const userData = await api.user.me();
                setUser(userData);
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            TokenManager.clearTokens();
        } finally {
            setIsLoading(false);
        }
    };

    const login = useCallback(async (email: string, password: string) => {
        setIsLoading(true);
        try {
            const response = await api.auth.login(email, password);
            TokenManager.setTokens(response.access, response.refresh);
            setUser(response.user);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const register = useCallback(async (data: RegisterData) => {
        setIsLoading(true);
        try {
            const response = await api.auth.register(data);
            TokenManager.setTokens(response.tokens.access, response.tokens.refresh);
            setUser(response.user);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const logout = useCallback(async () => {
        try {
            await api.auth.logout();
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            TokenManager.clearTokens();
            setUser(null);
        }
    }, []);

    const refreshUser = useCallback(async () => {
        try {
            const userData = await api.user.me();
            setUser(userData);
        } catch (error) {
            console.error('Failed to refresh user:', error);
        }
    }, []);

    const value: AuthContextType = {
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

// Hook to use auth context
export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

// Protected route component
export function RequireAuth({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        // Redirect to login
        window.location.href = '/login';
        return null;
    }

    return <>{children}</>;
}

export default AuthContext;
