import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ordersService } from '../services/orders.service';
import { documentsService } from '../services/documents.service';
import { LoadingState } from '../components/common/LoadingState';
import { StatusBadge } from '../components/common/StatusBadge';
import { LaunchVerificationModal } from '../components/common/LaunchVerificationModal';
import {
  Package,
  ShieldCheck,
  FileText,
  PlayCircle,
  ArrowLeft,
  DollarSign,
  MapPin,
  Calendar,
} from 'lucide-react';

export const OrderDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [verifyModalOpen, setVerifyModalOpen] = useState(false);

  const { data: order, isLoading, error } = useQuery({
    queryKey: ['order', id],
    queryFn: () => ordersService.getOrder(id!),
    enabled: !!id,
  });

  const { data: relatedDocs = [] } = useQuery({
    queryKey: ['documents', id],
    queryFn: () => documentsService.getDocuments({ order_id: id }),
    enabled: !!id,
  });

  if (isLoading) {
    return <LoadingState message="Loading approved order baseline..." />;
  }

  if (error || !order) {
    return (
      <div className="p-8 text-center text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl">
        Failed to load order '{id}'.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <Link
            to="/orders"
            className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 transition mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Orders</span>
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight text-slate-900">
              {order.customer_name} ({order.id})
            </h1>
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Ground Truth Baseline
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Destination: <span className="font-semibold text-slate-700">{order.destination}</span> &bull; Version {order.version}
          </p>
        </div>

        <button
          onClick={() => setVerifyModalOpen(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition"
        >
          <PlayCircle className="w-4 h-4" />
          <span>Verify Documents Against This Order</span>
        </button>
      </div>

      {/* Financial & Contract Summary Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card-subtle p-3.5">
          <span className="text-[10px] uppercase font-bold text-slate-400 block">Authorized Grand Total</span>
          <span className="text-lg font-bold text-slate-900 font-mono mt-1 block text-blue-700">
            {order.currency} {Number(order.grand_total).toLocaleString()}
          </span>
        </div>
        <div className="card-subtle p-3.5">
          <span className="text-[10px] uppercase font-bold text-slate-400 block">Total Quantity</span>
          <span className="text-lg font-bold text-slate-900 font-mono mt-1 block">
            {order.quantity != null ? `${order.quantity.toLocaleString()} PCS` : '—'}
          </span>
        </div>
        <div className="card-subtle p-3.5">
          <span className="text-[10px] uppercase font-bold text-slate-400 block">Contract Unit Price</span>
          <span className="text-lg font-bold text-slate-900 font-mono mt-1 block">
            {order.unit_price != null && !isNaN(Number(order.unit_price)) ? `$${Number(order.unit_price).toFixed(2)}` : '—'}
          </span>
        </div>
        <div className="card-subtle p-3.5">
          <span className="text-[10px] uppercase font-bold text-slate-400 block">Package Count</span>
          <span className="text-lg font-bold text-slate-900 font-mono mt-1 block">
            {order.package_count || 'Unspecified'} PKGS
          </span>
        </div>
      </div>

      {/* Order Items Table */}
      {(() => {
        const items = order.items || [];
        return (
          <div className="card-subtle overflow-hidden">
            <div className="p-4 border-b border-slate-200 bg-slate-50/75">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Approved Line Items ({items.length})
              </h3>
            </div>
            <div className="overflow-x-auto">
              {items.length === 0 ? (
                <p className="p-4 text-xs text-slate-400 text-center">No line items recorded for this order.</p>
              ) : (
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50/50">
                      <th className="table-th">SKU</th>
                      <th className="table-th">Product Description</th>
                      <th className="table-th">Quantity</th>
                      <th className="table-th">Unit Price</th>
                      <th className="table-th">Line Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {items.map((it, idx) => (
                      <tr key={it.id || idx} className="hover:bg-slate-50/60">
                        <td className="table-td font-mono font-semibold text-slate-800">{it.sku || 'N/A'}</td>
                        <td className="table-td text-slate-700">{it.description}</td>
                        <td className="table-td font-mono text-slate-800">
                          {it.quantity != null ? it.quantity : '—'} {it.unit || ''}
                        </td>
                        <td className="table-td font-mono text-slate-700">
                          {it.unit_price != null && !isNaN(Number(it.unit_price)) ? `$${Number(it.unit_price).toFixed(2)}` : '—'}
                        </td>
                        <td className="table-td font-mono font-bold text-slate-900">
                          {it.line_total != null && !isNaN(Number(it.line_total)) ? `$${Number(it.line_total).toFixed(2)}` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        );
      })()}

      {/* Associated Ingested Documents */}
      <div className="card-subtle p-5 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
          Associated Commercial Documents ({relatedDocs.length})
        </h3>
        {relatedDocs.length === 0 ? (
          <p className="text-xs text-slate-400">
            No commercial documents linked to this order yet.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {relatedDocs.map((doc) => (
              <div
                key={doc.id}
                className="p-3.5 rounded-lg border border-slate-200 hover:border-slate-300 bg-slate-50/50 flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <div>
                    <Link
                      to={`/documents/${doc.id}`}
                      className="font-semibold text-slate-900 hover:text-blue-600"
                    >
                      {doc.original_filename}
                    </Link>
                    <p className="text-[10px] text-slate-400 capitalize">
                      {doc.document_type.replace('_', ' ')} &bull; {doc.page_count} pages
                    </p>
                  </div>
                </div>
                <StatusBadge status={doc.status} size="sm" />
              </div>
            ))}
          </div>
        )}
      </div>

      <LaunchVerificationModal
        isOpen={verifyModalOpen}
        preselectedOrderId={order.id}
        onClose={() => setVerifyModalOpen(false)}
      />
    </div>
  );
};

