/**
 * Authentication utilities for managing JWT tokens and user sessions
 */

// Get token from either localStorage or sessionStorage
function getToken() {
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
}

// Get token type
function getTokenType() {
    return localStorage.getItem('token_type') || sessionStorage.getItem('token_type') || 'bearer';
}

// Get stored user info
function getUser() {
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// Check if user is authenticated
function isAuthenticated() {
    return !!getToken();
}

// Logout user
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('user');
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('token_type');
    sessionStorage.removeItem('user');
    
    console.log('User logged out');
}

// Make authenticated API request
async function authenticatedFetch(url, options = {}) {
    const token = getToken();
    const tokenType = getTokenType();
    
    if (!token) {
        throw new Error('No authentication token found');
    }
    
    const headers = {
        ...options.headers,
        'Authorization': `${tokenType} ${token}`
    };
    
    const response = await fetch(url, {
        ...options,
        headers
    });
    
    // If unauthorized, clear tokens and redirect to login
    if (response.status === 401) {
        logout();
        window.location.href = '/static/login.html';
        throw new Error('Authentication failed');
    }
    
    return response;
}

// Decode JWT token (simple base64 decode - for display purposes only)
function decodeToken(token) {
    try {
        const payload = token.split('.')[1];
        const decoded = atob(payload);
        return JSON.parse(decoded);
    } catch (error) {
        console.error('Error decoding token:', error);
        return null;
    }
}

// Check if token is expired
function isTokenExpired(token) {
    const decoded = decodeToken(token);
    if (!decoded || !decoded.exp) {
        return true;
    }
    
    const now = Math.floor(Date.now() / 1000);
    return decoded.exp < now;
}

// Validate current session
function validateSession() {
    const token = getToken();
    
    if (!token) {
        return false;
    }
    
    if (isTokenExpired(token)) {
        console.log('Token expired, logging out...');
        logout();
        return false;
    }
    
    return true;
}

// Require authentication (redirect to login if not authenticated)
function requireAuth(redirectUrl = '/static/login.html') {
    if (!validateSession()) {
        window.location.href = redirectUrl;
        return false;
    }
    return true;
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getToken,
        getTokenType,
        getUser,
        isAuthenticated,
        logout,
        authenticatedFetch,
        decodeToken,
        isTokenExpired,
        validateSession,
        requireAuth
    };
}
