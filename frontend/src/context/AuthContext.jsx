import React, { createContext, useState, useEffect, useContext } from 'react';
import client from '../api/client';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            // Ideally verify token with backend, for now just assume logged in if token exists
            // or decode it. For simplicity, we'll just set a flag or try to fetch user profile if endpoint exists
            // But we don't have a /me endpoint yet. Let's just persist the token.
            setUser({ token });
        }
        setLoading(false);
    }, []);

    const login = async (email, password) => {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        const response = await client.post('/auth/token', formData);
        const { access_token } = response.data;

        localStorage.setItem('token', access_token);
        setUser({ token: access_token, email });
        return true;
    };

    const register = async (email, password) => {
        await client.post('/auth/register', { email, password });
        return true;
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, register, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
