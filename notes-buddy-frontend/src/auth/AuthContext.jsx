import { createContext, useContext, useState, useEffect} from "react";

const AuthContext = createContext(null);

export const AuthProvider = ({ children}) => {
    const [token, setToken] = useState(
        () => localStorage.getItem("access_token")
    );

    const login = (accessToken, refreshToken) => {
        localStorage.setItem("access_token", accessToken);
        if (refreshToken) {
            localStorage.setItem("refresh_token", refreshToken);
        }
        setToken(accessToken);
    };

    const logout = () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        setToken(null);
    };

    return (
        <AuthContext.Provider value={{ token, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    return useContext(AuthContext);
};
