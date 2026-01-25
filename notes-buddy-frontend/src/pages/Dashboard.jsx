import { useEffect, useState } from 'react';
import { fetchDocuments } from '../api/documents';
import UploadForm from '../components/UploadForm';
import  DocumentList from '../components/DocumentList';

export default function Dashboard() {
    const [documents, setDocuments] = useState([]);
    const loadDocuments = async () => {
        const data = await fetchDocuments();
        setDocuments(data);
    };

    useEffect(() =>{
        loadDocuments();

        const interval = setInterval(loadDocuments, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-6 max-w-3xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">Notes Buddy</h1>

            <UploadForm onUpload={loadDocuments} />
            <DocumentList documents={documents} />
        </div>
    );
}