import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [currUser, setCurrUser] = useState(false)
    useEffect(() => {
        // Check if user is already authenticated
        const authStatus = localStorage.getItem('isAuthenticated');
        const user = localStorage.getItem('Email');
        setIsAuthenticated(authStatus === 'true');
        setCurrUser(user);
    }, []);

    const login = (email) => {
        setIsAuthenticated(true);
        localStorage.setItem('isAuthenticated', 'true');
        localStorage.setItem('Email', email);
        
    };

    const logout = () => {
        setIsAuthenticated(false);
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('Email');
    };

    return (
        <AuthContext.Provider value={{ isAuthenticated,currUser, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}
