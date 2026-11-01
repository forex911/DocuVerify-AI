import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ordersService, CreateOrderPayload } from '../services/orders.service';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';
import { Modal } from '../components/common/Modal';
import { useUIStore } from '../store/uiStore';
import {
  Package,
  Plus,
  Search,
  ShieldCheck,
  CheckCircle,
  FileText,
  DollarSign,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const Orders: React.FC = () => {
  const queryClient = useQueryClient();
  const { showNotification } = useUIStore();
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);

  // Form state for creating order
  const [orderId, setOrderId] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [quantity, setQuantity] = useState(1000);
  const [unitPrice, setUnitPrice] = useState(25.0);
  const [subtotal, setSubtotal] = useState(25000.0);
  const [tax, setTax] = useState(0.0);
  const [freight, setFreight] = useState(0.0);
  const [grandTotal, setGrandTotal] = useState(25000.0);
  const [destination, setDestination] = useState('Chennai Port, India');
  const [packageCount, setPackageCount] = useState(40);
  const [itemSku, setItemSku] = useState('PROD-INDUSTRIAL-01');
  const [itemDesc, setItemDesc] = useState('Industrial Machined Components Grade-A');
  const [itemUnit, setItemUnit] = useState('PCS');

  const { data: orders = [], isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: ordersService.getOrders,
  });

  const createMutation = useMutation({
    mutationFn: (payload: CreateOrderPayload) => ordersService.createOrder(payload),
    onSuccess: (data) => {
      showNotification(`Authoritative order '${data.id}' created.`, 'success');
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
      setModalOpen(false);
    },
    onError: (err: any) => {
      showNotification(err.message || 'Failed to create order', 'error');
    },
  });

  const handleCreateOrder = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      order_id: orderId.trim() || undefined,
      customer_name: customerName.trim(),
      currency,
      quantity: Number(quantity),
      unit_price: Number(unitPrice),
      subtotal: Number(subtotal),
      tax: Number(tax),
      freight: Number(freight),
      grand_total: Number(grandTotal),
      destination: destination.trim(),
      package_count: Number(packageCount),
      is_authoritative: true,
      items: [
        {
          sku: itemSku.trim(),
          description: itemDesc.trim(),
          quantity: Number(quantity),
          unit: itemUnit.trim(),
          unit_price: Number(unitPrice),
          line_total: Number(subtotal),
        },
      ],
    });
  };

  const filteredOrders = orders.filter((o) => {
    const q = search.toLowerCase();
    return (
      (o.id || '').toLowerCase().includes(q) ||
      (o.customer_name || '').toLowerCase().includes(q) ||
      (o.destination || '').toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Approved Customer Orders
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Authoritative baseline source-of-truth used by the deterministic verification engine.
          </p>
        </div>

        <button
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>New Approved Order</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="card-subtle p-3 bg-white">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by order ID, customer name, destination port..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
          />
        </div>
      </div>

      {/* Orders Table */}
      {isLoading ? (
        <LoadingState message="Loading approved orders registry..." />
      ) : filteredOrders.length === 0 ? (
        <EmptyState
          icon={Package}
          title="No approved orders found"
          description="Register an authoritative purchase order to serve as the baseline ground truth."
          actionText="Create Order"
          onAction={() => setModalOpen(true)}
        />
      ) : (
        <div className="card-subtle overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75">
                  <th className="table-th">Order Reference</th>
                  <th className="table-th">Customer Name</th>
                  <th className="table-th">Authorized Destination</th>
                  <th className="table-th">Quantity</th>
                  <th className="table-th">Unit Price</th>
                  <th className="table-th">Grand Total</th>
                  <th className="table-th">Authoritative</th>
                  <th className="table-th">Created</th>
                  <th className="table-th text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredOrders.map((ord) => (
                  <tr key={ord.id} className="hover:bg-slate-50/60 transition">
                    <td className="table-td">
                      <div className="flex items-center gap-2">
                        <Package className="w-4 h-4 text-blue-600 shrink-0" />
                        <div>
                          <span className="font-mono font-bold text-slate-900 block">
                            {ord.id}
                          </span>
                          <span className="text-[10px] text-slate-400">v{ord.version}</span>
                        </div>
                      </div>
                    </td>

                    <td className="table-td font-semibold text-slate-800">
                      {ord.customer_name}
                    </td>

                    <td className="table-td text-slate-700">
                      {ord.destination}
                    </td>

                    <td className="table-td font-mono text-slate-800">
                      {ord.quantity.toLocaleString()} PCS
                    </td>

                    <td className="table-td font-mono text-slate-700">
                      ${Number(ord.unit_price).toFixed(2)}
                    </td>

                    <td className="table-td font-mono font-bold text-slate-900 text-sm">
                      {ord.currency} {Number(ord.grand_total).toLocaleString()}
                    </td>

                    <td className="table-td">
                      {ord.is_authoritative ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Authoritative
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[11px]">Draft</span>
                      )}
                    </td>

                    <td className="table-td text-slate-400 text-[11px]">
                      {new Date(ord.created_at).toLocaleDateString()}
                    </td>

                    <td className="table-td text-right">
                      <Link
                        to={`/orders/${ord.id}`}
                        className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 font-semibold text-xs"
                      >
                        <span>Details</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Order Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Register Approved Customer Order"
        subtitle="Authoritative contract baseline against which commercial documents are verified."
        maxWidth="2xl"
      >
        <form onSubmit={handleCreateOrder} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Order Reference / PO ID <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={orderId}
                onChange={(e) => setOrderId(e.target.value)}
                placeholder="e.g. ORD-10245"
                className="w-full text-xs rounded-lg border border-slate-200 p-2 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Customer Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="e.g. ABC Industries Ltd"
                className="w-full text-xs rounded-lg border border-slate-200 p-2"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Currency <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={currency}
                onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                placeholder="USD"
                className="w-full text-xs rounded-lg border border-slate-200 p-2 font-mono uppercase"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Total Quantity <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                required
                value={quantity}
                onChange={(e) => {
                  const q = Number(e.target.value);
                  setQuantity(q);
                  setSubtotal(q * unitPrice);
                  setGrandTotal(q * unitPrice + tax + freight);
                }}
                className="w-full text-xs rounded-lg border border-slate-200 p-2 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Unit Price <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={unitPrice}
                onChange={(e) => {
                  const p = Number(e.target.value);
                  setUnitPrice(p);
                  setSubtotal(quantity * p);
                  setGrandTotal(quantity * p + tax + freight);
                }}
                className="w-full text-xs rounded-lg border border-slate-200 p-2 font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Subtotal Amount
              </label>
              <input
                type="number"
                step="0.01"
                value={subtotal}
                onChange={(e) => setSubtotal(Number(e.target.value))}
                className="w-full text-xs rounded-lg border border-slate-200 p-2 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Tax / Freight
              </label>
              <input
                type="number"
                step="0.01"
                value={tax + freight}
                onChange={(e) => {
                  const tf = Number(e.target.value);
                  setTax(tf);
                  setGrandTotal(subtotal + tf);
                }}
                className="w-full text-xs rounded-lg border border-slate-200 p-2 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Grand Total <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={grandTotal}
                onChange={(e) => setGrandTotal(Number(e.target.value))}
                className="w-full text-xs rounded-lg border border-slate-200 p-2 font-mono font-bold text-blue-700"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Approved Destination / Port <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="e.g. Chennai Port, India"
                className="w-full text-xs rounded-lg border border-slate-200 p-2"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Expected Package Count
              </label>
              <input
                type="number"
                value={packageCount}
                onChange={(e) => setPackageCount(Number(e.target.value))}
                className="w-full text-xs rounded-lg border border-slate-200 p-2 font-mono"
              />
            </div>
          </div>

          {/* Line item info */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Default Line Item
            </span>
            <div className="grid grid-cols-3 gap-2">
              <input
                type="text"
                placeholder="SKU"
                value={itemSku}
                onChange={(e) => setItemSku(e.target.value)}
                className="text-xs p-1.5 rounded border border-slate-200 font-mono"
              />
              <input
                type="text"
                placeholder="Description"
                value={itemDesc}
                onChange={(e) => setItemDesc(e.target.value)}
                className="text-xs p-1.5 rounded border border-slate-200 col-span-2"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg shadow-sm transition"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  <span>Save Approved Order</span>
                </>
              )}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

