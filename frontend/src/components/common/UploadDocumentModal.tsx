import React, { useState } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle, FileText, Loader2 } from 'lucide-react';
import { Modal } from './Modal';
import { documentsService } from '../../services/documents.service';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ordersService } from '../../services/orders.service';
import { useUIStore } from '../../store/uiStore';

interface UploadDocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploaded?: (docId: string) => void;
}

export const UploadDocumentModal: React.FC<UploadDocumentModalProps> = ({
  isOpen,
  onClose,
  onUploaded,
}) => {
  const queryClient = useQueryClient();
  const { showNotification } = useUIStore();
  const [file, setFile] = useState<File | null>(null);
  const [orderId, setOrderId] = useState<string>('');
  const [documentType, setDocumentType] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: orders = [] } = useQuery({
    queryKey: ['orders'],
    queryFn: ordersService.getOrders,
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (selected.type !== 'application/pdf') {
        setError('Only PDF documents are supported for commercial verification.');
        return;
      }
      setFile(selected);
      setError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const dropped = e.dataTransfer.files[0];
      if (dropped.type !== 'application/pdf') {
        setError('Only PDF documents are supported for commercial verification.');
        return;
      }
      setFile(dropped);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a commercial PDF to upload.');
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      const res = await documentsService.uploadDocument(
        file,
        orderId || undefined,
        documentType || undefined
      );
      showNotification(`Successfully uploaded ${res.original_filename}`, 'success');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      setFile(null);
      setOrderId('');
      setDocumentType('');
      onClose();
      if (onUploaded) onUploaded(res.id);
    } catch (err: any) {
      setError(err.message || 'Failed to upload document');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Upload Commercial Document"
      subtitle="PDF ingestion with page-by-page text extraction and structured parsing."
      maxWidth="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-700">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Drag and Drop Box */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer ${
            file
              ? 'border-blue-300 bg-blue-50/30'
              : 'border-slate-200 hover:border-blue-400 bg-slate-50/50'
          }`}
        >
          <input
            type="file"
            id="pdf-upload"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            className="hidden"
          />
          <label htmlFor="pdf-upload" className="cursor-pointer block">
            {file ? (
              <div className="flex flex-col items-center">
                <FileText className="w-10 h-10 text-blue-600 mb-2" />
                <p className="text-sm font-semibold text-slate-800">{file.name}</p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {(file.size / 1024).toFixed(1)} KB &bull; Ready for ingestion
                </p>
                <span className="mt-2 text-xs text-blue-600 hover:underline">Choose a different file</span>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <UploadCloud className="w-10 h-10 text-slate-400 mb-2" />
                <p className="text-sm font-semibold text-slate-700">Click or drag PDF document here</p>
                <p className="text-xs text-slate-400 mt-1">Invoices, Packing Lists, Bills of Lading (Max 20MB)</p>
              </div>
            )}
          </label>
        </div>

        {/* Optional Document Type Hint */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Document Type (Optional Auto-Classification Hint)
          </label>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          >
            <option value="">Auto-Detect via AI Intelligence Agent</option>
            <option value="invoice">Commercial Invoice</option>
            <option value="packing_list">Packing List</option>
            <option value="bill_of_lading">Bill of Lading (BOL)</option>
          </select>
        </div>

        {/* Associated Approved Order */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Associate with Approved Customer Order (Optional)
          </label>
          <select
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          >
            <option value="">Auto-Match during Multi-Agent Verification</option>
            {orders.map((o) => (
              <option key={o.id} value={o.id}>
                {o.id} &mdash; {o.customer_name} ({o.currency} {Number(o.grand_total).toLocaleString()})
              </option>
            ))}
          </select>
        </div>

        {/* Notice */}
        <p className="text-[11px] text-slate-400 leading-normal">
          Documents are processed through deterministic OCR & parsing pipelines. The file is hashed for cryptographic integrity.
        </p>

        {/* Buttons */}
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!file || isUploading}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg shadow-sm transition"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Ingesting PDF...</span>
              </>
            ) : (
              <>
                <UploadCloud className="w-4 h-4" />
                <span>Upload & Ingest</span>
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};

