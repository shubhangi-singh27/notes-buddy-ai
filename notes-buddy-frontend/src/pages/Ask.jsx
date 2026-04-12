import {useState} from "react";
import api from "../api/axios";

export default function Ask() {
    const[question, setQuestion] = useState("");
    const[answer, setAnswer] = useState("");
    const[loading, setLoading] = useState(false);

    const handleAsk = async() => {
        if(!question.trim()) return;

        setLoading(true);
        setAnswer(null);

        try {
            const res = await api.post("/search/answer/", {
                question: question,
                document_id: null,
            });

            setAnswer(res.data);
        } catch(err) {
            console.error("Error asking question:", err);
            alert("Failed to get answer. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-3l mx-auto mt-10">
            <h1 className="text-2xl font=bold mb-4">Ask Notes Buddy</h1>

            <textarea
                className="w-full border rounded p-3"
                rows="3"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        if (question.trim() && !loading) {
                            handleAsk();
                        }
                    }
                }}
                placeholder="Ask me anything about your notes..."
            />

            <button 
                onClick={handleAsk}
                className="mt-3 px-4 py-2 bg-blue-600 text-white rounded"
            >
                {loading ? "Thinking..." : "Ask Notes Buddy"}
            </button>

            {answer && (
                <div className="mt-6 border rounded p-4 bg-gray-100">
                    <h2 className="font-semibold mb-2">Answer</h2>
                    <p className="whitespace-pre-wrap">{answer.answer}</p>

                    <h3 className="mt-4 font-semibold">Sources</h3>
                    <ul className="list-disc ml-6">
                        {(answer.sources || []).map((s, i) => (
                            <li key={i}>
                                {typeof s === "object"
                                    ? `${s.document_name || "Unknown"} - chunk ${s.chunk_index ?? i}`
                                    : String(s)}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    )
}