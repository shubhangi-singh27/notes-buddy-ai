import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getDocumentDetail } from "../api/documents";
import api from "../api/axios";

export default function DocumentDetail() {
    const { id } = useParams();
    const [doc, setDoc] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState(null);
    const [sources, setSources] = useState([]);

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

    const handleAsk = async() => {
        setLoading(true);
        setError(null);
        setAnswer(null);
        setSources([]);

        try {
            const res = await api.post("/search/answer/", {
                question: question,
                document_id: id,
            });

            setAnswer(res.data.answer);
            setSources(res.data.sources || []);
        } catch (err) {
            setError("Failed to get answer, Try again.")
        } finally {
            setLoading(false);
        }
    };

    const isAskDisabled = 
        loading ||
        !doc ||
        doc.status !== "ready" ||
        !question.trim();

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
            <div className="mt-8 border-t pt-6">
                <h2 className="text-lg font-semibold mb-2">Ask a question</h2>

                <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            if (!isAskDisabled) {
                                handleAsk();
                            }
                        }
                    }}
                    placeholder="Ask something from this document..."
                    className="w-full border rounded p-3 mb-3"
                    rows={3}
                />

                <button
                    onClick={handleAsk}
                    disabled={isAskDisabled}
                    className="bg-black text-white px-4 py-2 rounded disabled:opacity-50"
                >
                    {loading ? "Thinking..." : "Ask"}
                </button>

            </div>
            {answer && (
                <div className="mt-6">
                    <h3 className="font-semibold mb-2">Answer</h3>
                    <p className="whitespace-pre-line">{answer}</p>

                    {sources.length > 0 && (
                        <div className="mt-4 text-sm text-gray-600">
                            <p className="font-medium">Sources:</p>
                            <ul className="list-disc ml-5">
                                {sources.map((s, i) => (
                                    <li key={i} className="relative group cursor-pointer">
                                        <span className="underline decoration-dotted">
                                            {s.document_name} - chunk {s.chunk_index}
                                        </span>
                                        {s.text && (
                                            <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block z-10 w-96 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
                                                <p className="font-semibold mb-1">
                                                    {s.document_name} (chunk {s.chunk_index})
                                                </p>
                                                <p className="whitespace-pre-wrap max-h-96 overflow-y-auto">
                                                    {s.text}
                                                </p>
                                            </div>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
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

            {error && (
                <p className="text-red-600 mt-4">{error}</p>
            )}
        </div>
    );
}