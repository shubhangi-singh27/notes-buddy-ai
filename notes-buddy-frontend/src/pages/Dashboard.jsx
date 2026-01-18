import {useAuth} from "../auth/AuthContext"

export default function Dashboard() {
    const{logout}  = useAuth();
    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4"> Notes Buddy Dashboard </h1>
            <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded"
            >
                Logout
            </button>
        </div>
    );
}