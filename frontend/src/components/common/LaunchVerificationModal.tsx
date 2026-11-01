import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlayCircle, AlertCircle, FileCheck, Loader2 } from 'lucide-react';
import { Modal } from './Modal';
import { workflowsService } from '../../services/workflows.service';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { documentsService } from '../../services/documents.service';
import { ordersService } from '../../services/orders.service';
import { useUIStore } from '../../store/uiStore';

interface LaunchVerificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedDocumentId?: string;
  preselectedOrderId?: string;
}

export const LaunchVerificationModal: React.FC<LaunchVerificationModalProps> = ({
  isOpen,
  onClose,
  preselectedDocumentId,
  preselectedOrderId,
}) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showNotification } = useUIStore();
  const [selectedDocs, setSelectedDocs] = useState<string[]>(
    preselectedDocumentId ? [preselectedDocumentId] : []
  );
  const [selectedOrder, setSelectedOrder] = useState<string>(preselectedOrderId || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: documents = [] } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsService.getDocuments(),
    enabled: isOpen,
  });

  const { data: orders = [] } = useQuery({
    queryKey: ['orders'],
    queryFn: ordersService.getOrders,
    enabled: isOpen,
  });

  const toggleDoc = (docId: string) => {
    setSelectedDocs((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const isAllSelected = documents.length > 0 && selectedDocs.length === documents.length;
  const isIndeterminate = selectedDocs.length > 0 && selectedDocs.length < documents.length;

  const toggleSelectAll = () => {
    if (isAllSelected) {
      setSelectedDocs([]);
    } else {
      setSelectedDocs(documents.map((d) => d.id));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedDocs.length === 0) {
      setError('Select at least one commercial document to verify.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      const res = await workflowsService.initiateWorkflow({
        document_ids: selectedDocs,
        order_id: selectedOrder || undefined,
        run_async: true,
      });

      showNotification('Multi-agent verification workflow initiated.', 'success');
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      onClose();
      // Navigate to the verification workspace for this workflow
      navigate(`/verification/${res.workflow_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to initiate verification workflow');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Launch Multi-Agent Verification"
      subtitle="Orchestrates Supervisor, Document Intelligence, Order Matching, Validation, Reconciliation, and Explanation Agents."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-700">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Select Documents */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-semibold text-slate-700">
              Select Documents to Verify ({selectedDocs.length} of {documents.length} selected)
            </label>
            {documents.length > 0 && (
              <label className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 font-semibold cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  ref={(input) => {
                    if (input) input.indeterminate = isIndeterminate;
                  }}
                  onChange={toggleSelectAll}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-3.5 h-3.5 cursor-pointer"
                />
                <span>Select All</span>
              </label>
            )}
          </div>
          <div className="max-h-52 overflow-y-auto border border-slate-200 rounded-lg divide-y divide-slate-100 bg-slate-50/50">
            {documents.length === 0 ? (
              <p className="p-4 text-xs text-slate-500 text-center">
                No uploaded documents found. Please upload a commercial document first.
              </p>
            ) : (
              documents.map((doc) => (
                <label
                  key={doc.id}
                  className="flex items-center gap-3 p-2.5 hover:bg-slate-100/70 cursor-pointer transition"
                >
                  <input
                    type="checkbox"
                    checked={selectedDocs.includes(doc.id)}
                    onChange={() => toggleDoc(doc.id)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-slate-800 truncate">
                      {doc.original_filename}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      Type: <span className="uppercase">{doc.document_type}</span> &bull; Status:{' '}
                      {doc.status}
                    </p>
                  </div>
                </label>
              ))
            )}
          </div>
        </div>

        {/* Select Approved Order (Optional) */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Baseline Approved Customer Order
          </label>
          <select
            value={selectedOrder}
            onChange={(e) => setSelectedOrder(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          >
            <option value="">Auto-Detect Order via Order Matching Agent</option>
            {orders.map((o) => (
              <option key={o.id} value={o.id}>
                {o.id} &mdash; {o.customer_name} ({o.currency} {Number(o.grand_total).toLocaleString()})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-1">
            If left unselected, the Order Matching Agent will extract PO reference numbers from the documents and locate the authoritative order.
          </p>
        </div>

        <div className="rounded-lg bg-blue-50/60 border border-blue-200/60 p-3 text-xs text-blue-800">
          <p className="font-semibold mb-0.5">Automated Multi-Agent Pipeline</p>
          <p className="text-[11px] text-blue-700 leading-relaxed">
            The agents extract page-by-page data, execute deterministic verification rules (QTY-001, FIN-001, DEST-001, etc.), reconcile multi-document sets, and flag discrepancies for human review.
          </p>
        </div>

        {/* Footer actions */}
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
            disabled={selectedDocs.length === 0 || isSubmitting}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg shadow-sm transition"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Launching Agents...</span>
              </>
            ) : (
              <>
                <PlayCircle className="w-4 h-4" />
                <span>Start Verification</span>
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};

