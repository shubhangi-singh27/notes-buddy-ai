import { createContext, useContext, useState, useEffect} from "react";

const AuthContext = createContext(null);

export const AuthProvider = ({ children}) => {
    const [token, setToken] = useState(
        () => localStorage.getItem("access_token")
    );

    const login = (accessToken) => {
        localStorage.setItem("access_token", accessToken);
        setToken(accessToken);
    };

    const logout = () => {
        localStorage.removeItem("access_token");
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
