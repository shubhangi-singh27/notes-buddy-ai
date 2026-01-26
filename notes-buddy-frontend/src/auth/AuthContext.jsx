import { createContext, useContext, useState, useEffect} from "react";
import api from "../api/axios";

const AuthContext = createContext(null);

export const AuthProvider = ({ children}) => {
    const [token, setToken] = useState(
        () => localStorage.getItem("access_token")
    );
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const currentToken = localStorage.getItem("access_token")
        if (!currentToken) {
            setUser(null)
            setLoading(false)
            return
        }

        setLoading(true);
        api.get("/users/me/")
            .then(res => setUser(res.data))
            .catch(() => {
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                setUser(null);
                setToken(null);
            })
            .finally(() => setLoading(false));
    }, [token])

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
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ token, user, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    return useContext(AuthContext);
};
