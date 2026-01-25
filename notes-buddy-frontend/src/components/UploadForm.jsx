import { useState } from 'react';
import { uploadDocument } from '../api/documents';

export default function UploadForm({ onUpload }){
    const[file, setFile] = useState(null);
    const[loading, setLoading] = useState(false);
    const[error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) return;

        setLoading(true);
        setError(null);
        try {
            await uploadDocument(file);
            setFile(null);
            onUpload();
        } catch(err) {
            let errorMessage = "Upload failed.";

            if (err.response) {
                const status = err.response.status;
                const data = err.response.data;

                if (status==400) {
                    errorMassage = data.error || data.message ||
                            Object.values(data).flat().join(", ") ||
                            "Invalid file. Please check file type and size.";
                } else if (status == 401) {
                    errorMessage = "Session expired. Please login again.";
                }
            } else if (err.request) {
                errorMessage = "Network error. Please check your connection.";
            } else {
                errorMessage = err.message || "An unknown error occurred.";
            }

            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="mb-6">
            <input
                type="file"
                onChange={(e) => {
                    setFile(e.target.files[0]);
                    setError(null);
                }}
                className="mb-2"
            />
            {error && (
                <div className="text-red-500 text-sm mb-2">
                    {error}
                </div>
            )}
            <button
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-2 rounded"
            >
                {loading ? "Uploading..." : "Upload"}
            </button>
        </form>
    )
}