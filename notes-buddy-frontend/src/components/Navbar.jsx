import { useAuth } from "../auth/AuthContext"
import { useNavigate } from "react-router-dom"

export default function Navbar() {
    const { user, logout, loading } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout()
        navigate("/login")
    }

    return (
        <div className="w-full h-14 bg-gray-900 text-white flex items-center justify-between px-6">
            <div className="font-semibold text-lg">
                Notes Buddy
            </div>

            {user && (
                <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-300">
                        {user.username}
                    </span>
                    <button
                        onClick={handleLogout}
                        className="px-2 py-1 rounded bg-red-600 hover:bg-red-700 text-sm"
                    >
                        Logout
                    </button>
                </div>
            )}
        </div>
    )
}