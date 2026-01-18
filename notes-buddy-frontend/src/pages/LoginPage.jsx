import {useState} from "react";
import {useNavigate} from "react-router-dom";
import api from "../api/axios";
import {useAuth} from "../auth/AuthContext";

export default function LoginPage(){
    const {login} = useAuth();
    const navigate = useNavigate();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");

        try{
            const res = await api.post("/users/login/", {
                username, 
                password,
            });
            login(res.data.access);
            navigate("/");
        } catch(err) {
            const errorMessage = err.response?.data?.detail ||
                                err.response?.data?.message ||
                                "Invalid credentials";
            setError(errorMessage);
        }
    };

    return (
        <div className="h-screen flex items-center justify-center">
            <form onSubmit={handleSubmit} className="p-6 border rounded w-80">
                <h2 className="text-xl mb-4">Login</h2>
                {error && <p className="text-red-500">{error}</p>}

                <input
                    className="border p-2 w-full mb-2"
                    type="text"
                    placeholder="Username or Email"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                />
                <input 
                    className="border p-2 w-full mb-4"
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />

                <button type="submit" className="bg-black text-white px-4 py-2 w-full">
                    Login
                </button>
            </form>
        </div>
    );
}