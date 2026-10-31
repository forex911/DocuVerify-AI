import { apiClient } from './api';
import { DocumentItem } from '../types';

export interface DocumentListParams {
  order_id?: string;
  document_type?: string;
  status?: string;
}

export const documentsService = {
  getDocuments: async (params?: DocumentListParams): Promise<DocumentItem[]> => {
    const res = await apiClient.get<DocumentItem[]>('/documents', { params });
    return res.data;
  },

  getDocument: async (documentId: string): Promise<DocumentItem> => {
    const res = await apiClient.get<DocumentItem>(`/documents/${documentId}`);
    return res.data;
  },

  getDocumentExtraction: async (documentId: string) => {
    const res = await apiClient.get(`/documents/${documentId}/extraction`);
    return res.data;
  },

  uploadDocument: async (
    file: File,
    orderId?: string,
    documentType?: string
  ): Promise<DocumentItem> => {
    const formData = new FormData();
    formData.append('file', file);
    if (orderId) formData.append('order_id', orderId);
    if (documentType) formData.append('document_type', documentType);

    const res = await apiClient.post<DocumentItem>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  getDocumentFileUrl: (documentId: string): string => {
    return `/api/documents/${documentId}/file`;
  },
};

