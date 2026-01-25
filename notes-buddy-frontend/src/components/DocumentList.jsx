export default function DocumentList({ documents }) {
    const formatDate = (dateString) => {
        if (!dateString) return "N/A";

        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs/60000);
        const diffHours = Math.floor(diffMs/3600000);
        const diffDays = Math.floor(diffMs/86400000);

        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 60) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 60) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };
    return (
        <div>
            <h2 className="text-xl font-semibold mb-4">Your Documents</h2>

            <ul className="space-y-2">
                {documents.map((doc) => (
                    <li
                        key={doc.id}
                        className="border p-3 rounded flex justify-between"
                    >
                        <div className="flex-1">
                            <div className="font-medium">{doc.original_file_name}</div>
                            <div className="text-sm text-gray-500">
                                Uploaded {formatDate(doc.created_at)}
                            </div>
                        </div>
                        <span className="text-sm text-gray-600">
                            {doc.status}
                        </span>
                    </li>
                ))}
            </ul>
        </div>
    )
}