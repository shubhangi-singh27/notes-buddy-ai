import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getDocumentDetail } from "../api/documents";

export default function DocumentDetail() {
    const { id } = useParams();
    const [doc, setDoc] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchDocument = async () => {
            setLoading(true);
            try {
                const res = await getDocumentDetail(id)
                setDoc(res.data);
                setError(null);
            } catch (err) {
                if (err.response?.status === 404) {
                    setError("Document not found");
                } else if (err.response?.status === 403) {
                    setError("You are not authorized to access this document");
                } else {
                    setError("Failed to load document");
                }
            } finally {
                setLoading(false);
            }
        }

        fetchDocument();
    }, [id]);

    if (loading) return <p>Loading Document...</p>;
    if (error) return <p className="text-red-500">{error}</p>;
    if (!doc) return <p>No document detail available</p>;

    return (
        <div className="p-6 space-y-4">
            <h1 className="text-xl font-semibold">
                {doc.original_file_name}
            </h1>
            <div className="text-sm text-gray-600">
                <p>Status: <span className="font-medium">{doc.status}</span></p>
                <p>Uploaded: {new Date(doc.created_at).toLocaleString()}</p>
                <p>
                    Total Chunks: <span className="font-medium">{doc.chunks?.length || 0}</span>
                    {doc.chunks && doc.chunks.length > 0 && (
                        <span className="ml-2 text-gray-500">
                            ({doc.chunks.filter(c => c.has_embedding).length} embedded)
                        </span>
                    )}
                </p>
            </div>
            <div className="mt-6">
                <h2 className="font-semibold">Short Summary</h2>
                <p className="text-gray-800 mt-2">
                    {doc.short_summary || "Summary not generated yet."}
                </p>
            </div>
            <div className="mt-6">
                <h2 className="font-semibold">Detailed Summary</h2>
                <p className="text-gray-800 mt-2 whitespace-pre-wrap">
                    {doc.detailed_summary || "Detailed summary not generated yet."}
                </p>
            </div>
        </div>
    );
}