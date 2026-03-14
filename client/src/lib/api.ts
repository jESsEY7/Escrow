/**
 * API Client for Escrow Platform
 * Handles authentication, requests, and error handling
 */

// API Base URL - Django backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002/api';

// Token storage keys
const ACCESS_TOKEN_KEY = 'escrow_access_token';
const REFRESH_TOKEN_KEY = 'escrow_refresh_token';

/**
 * Token management
 */
export const TokenManager = {
    getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
    getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),

    setTokens: (access: string, refresh: string) => {
        localStorage.setItem(ACCESS_TOKEN_KEY, access);
        localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
    },

    clearTokens: () => {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
    },

    hasTokens: () => !!localStorage.getItem(ACCESS_TOKEN_KEY),
};

/**
 * API Request helper with authentication
 */
async function apiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    // Add auth header if token exists
    const accessToken = TokenManager.getAccessToken();
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
    };

    if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const response = await fetch(url, {
        ...options,
        headers,
    });

    // Handle 401 - try to refresh token
    if (response.status === 401 && TokenManager.getRefreshToken()) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
            // Retry the original request
            headers['Authorization'] = `Bearer ${TokenManager.getAccessToken()}`;
            const retryResponse = await fetch(url, { ...options, headers });
            return handleResponse<T>(retryResponse);
        } else {
            // Refresh failed, clear tokens
            TokenManager.clearTokens();
            window.location.href = '/login';
            throw new Error('Session expired');
        }
    }

    return handleResponse<T>(response);
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Request failed' }));
        throw new Error(error.error || error.message || `HTTP ${response.status}`);
    }

    // Handle empty responses
    const text = await response.text();
    if (!text) return {} as T;

    return JSON.parse(text);
}

async function refreshAccessToken(): Promise<boolean> {
    try {
        const refreshToken = TokenManager.getRefreshToken();
        if (!refreshToken) return false;

        const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: refreshToken }),
        });

        if (!response.ok) return false;

        const data = await response.json();
        TokenManager.setTokens(data.access, data.refresh || refreshToken);
        return true;
    } catch {
        return false;
    }
}

/**
 * API Methods
 */
export const api = {
    // Auth
    auth: {
        register: (data: { email: string; password: string; password_confirm: string; first_name: string; last_name: string }) =>
            apiRequest<{ user: any; tokens: { access: string; refresh: string } }>('/auth/register/', {
                method: 'POST',
                body: JSON.stringify(data),
            }),

        login: (email: string, password: string) =>
            apiRequest<{ access: string; refresh: string; user: any }>('/auth/login/', {
                method: 'POST',
                body: JSON.stringify({ email, password }),
            }),

        logout: () =>
            apiRequest('/auth/logout/', {
                method: 'POST',
                body: JSON.stringify({ refresh: TokenManager.getRefreshToken() }),
            }).finally(() => TokenManager.clearTokens()),

        resetPassword: (email: string) =>
            apiRequest('/auth/password/reset/', {
                method: 'POST',
                body: JSON.stringify({ email }),
            }),
    },

    // User
    user: {
        me: () => apiRequest<any>('/users/me/'),

        update: (data: Partial<{ first_name: string; last_name: string; phone_number: string }>) =>
            apiRequest('/users/me/', {
                method: 'PATCH',
                body: JSON.stringify(data),
            }),

        changePassword: (data: { current_password: string; new_password: string; new_password_confirm: string }) =>
            apiRequest('/users/password/change/', {
                method: 'POST',
                body: JSON.stringify(data),
            }),

        submitKyc: (data: any) =>
            apiRequest('/users/kyc/submit/', {
                method: 'POST',
                body: JSON.stringify(data),
            }),

        kycStatus: () => apiRequest<any>('/users/kyc/status/'),
    },

    // Escrow
    escrow: {
        list: () => apiRequest<any[]>('/escrow/'),

        get: (id: string) => apiRequest<any>(`/escrow/${id}/`),

        create: (data: {
            title: string;
            description: string;
            escrow_type: string;
            total_amount: number;
            currency: string;
            milestones?: any[];
            seller_email?: string;
        }) =>
            apiRequest<any>('/escrow/', {
                method: 'POST',
                body: JSON.stringify(data),
            }),

        fund: (id: string, data: { payment_method: string; amount: number }) =>
            apiRequest<any>(`/escrow/${id}/fund/`, {
                method: 'POST',
                body: JSON.stringify(data),
            }),

        cancel: (id: string, reason?: string) =>
            apiRequest(`/escrow/${id}/cancel/`, {
                method: 'POST',
                body: JSON.stringify({ reason }),
            }),

        timeline: (id: string) => apiRequest<any[]>(`/escrow/${id}/timeline/`),

        // Milestones
        milestones: {
            list: (escrowId: string) => apiRequest<any[]>(`/escrow/${escrowId}/milestones/`),

            submit: (escrowId: string, milestoneId: string, data: { notes?: string }) =>
                apiRequest(`/escrow/${escrowId}/milestones/${milestoneId}/submit/`, {
                    method: 'POST',
                    body: JSON.stringify(data),
                }),

            approve: (escrowId: string, milestoneId: string) =>
                apiRequest(`/escrow/${escrowId}/milestones/${milestoneId}/approve/`, {
                    method: 'POST',
                }),

            reject: (escrowId: string, milestoneId: string, reason: string) =>
                apiRequest(`/escrow/${escrowId}/milestones/${milestoneId}/reject/`, {
                    method: 'POST',
                    body: JSON.stringify({ reason }),
                }),
        },
    },

    // Transactions
    transactions: {
        list: () => apiRequest<any[]>('/transactions/'),
        get: (id: string) => apiRequest<any>(`/transactions/${id}/`),
        my: () => apiRequest<any[]>('/transactions/my/'),
    },

    // M-Pesa Payments
    mpesa: {
        initiate: (escrowId: string, phoneNumber: string, amount: number) =>
            apiRequest<{ message: string; data: { checkout_request_id: string } }>('/transactions/mpesa/initiate/', {
                method: 'POST',
                body: JSON.stringify({
                    escrow_id: escrowId,
                    phone_number: phoneNumber,
                    amount,
                }),
            }),

        status: (checkoutRequestId: string) =>
            apiRequest<any>(`/transactions/mpesa/status/${checkoutRequestId}/`),

        query: (checkoutRequestId: string) =>
            apiRequest('/transactions/mpesa/query/', {
                method: 'POST',
                body: JSON.stringify({ checkout_request_id: checkoutRequestId }),
            }),
    },

    // Disputes
    disputes: {
        list: () => apiRequest<any[]>('/disputes/'),

        get: (id: string) => apiRequest<any>(`/disputes/${id}/`),

        create: (data: { escrow_id: string; reason: string; description: string; disputed_amount?: number }) =>
            apiRequest<any>('/disputes/', {
                method: 'POST',
                body: JSON.stringify(data),
            }),

        respond: (id: string, data: { content: string; accepts_claim?: boolean; counter_offer?: number }) =>
            apiRequest(`/disputes/${id}/respond/`, {
                method: 'POST',
                body: JSON.stringify(data),
            }),

        submitEvidence: (id: string, data: any) =>
            apiRequest(`/disputes/${id}/evidence/`, {
                method: 'POST',
                body: JSON.stringify(data),
            }),
    },
};

export default api;
