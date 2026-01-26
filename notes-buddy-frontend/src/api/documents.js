import api from "./axios";

export const fetchDocuments = async() => {
    const res = await api.get("/documents/");
    return res.data;
}

export const uploadDocument = async(file) => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await api.post("/documents/upload/", formData, {
        headers: { "Content-Type": "multipart/form-data" }
    });

    return res.data;
}

export const getDocumentDetail = (id) => {
    return api.get(`/documents/${id}/`);
}