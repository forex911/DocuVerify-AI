import React from 'react';
import { useUIStore } from '../store/uiStore';
import {
  Settings as SettingsIcon,
  UserCheck,
  ShieldAlert,
  Cpu,
  Sliders,
  CheckCircle2,
  Database,
  Lock,
} from 'lucide-react';

export const Settings: React.FC = () => {
  const { currentReviewer, setCurrentReviewer, showNotification } = useUIStore();

  const mockReviewers = [
    {
      id: 'rev_sarah_chen',
      name: 'Sarah Chen',
      role: 'Lead Verification Specialist',
      email: 'sarah.chen@docuverify.internal',
    },
    {
      id: 'rev_david_kumar',
      name: 'David Kumar',
      role: 'Senior Trade Compliance Officer',
      email: 'david.kumar@docuverify.internal',
    },
    {
      id: 'rev_elena_rostova',
      name: 'Elena Rostova',
      role: 'Director of Global Trade Operations',
      email: 'elena.rostova@docuverify.internal',
    },
  ];

  const handleSelectReviewer = (rev: typeof mockReviewers[0]) => {
    setCurrentReviewer(rev);
    showNotification(`Switched active reviewer to ${rev.name} (${rev.role})`, 'info');
  };

  const rules = [
    { id: 'ID-001', name: 'Order Reference Mismatch', sev: 'Critical', tol: 'Exact string match' },
    { id: 'REQ-001', name: 'Missing Required Field', sev: 'High', tol: 'Zero missing critical values' },
    { id: 'QTY-001', name: 'Quantity Mismatch', sev: 'High', tol: '0.00 units' },
    { id: 'FIN-001', name: 'Grand Total Mismatch', sev: 'High', tol: '$0.01 tolerance' },
    { id: 'FIN-002', name: 'Line Arithmetic Mismatch', sev: 'Medium', tol: 'Decimal precision' },
    { id: 'CUR-001', name: 'Currency Mismatch', sev: 'Critical', tol: 'Exact ISO currency code' },
    { id: 'DEST-001', name: 'Destination Mismatch', sev: 'Medium', tol: 'Normalized city / port string' },
    { id: 'XDOC-001', name: 'Cross-Doc Quantity Mismatch', sev: 'High', tol: 'Zero cross-doc variance' },
    { id: 'XDOC-002', name: 'Cross-Doc Package Count Mismatch', sev: 'Medium', tol: 'Exact package count' },
    { id: 'XDOC-003', name: 'Cross-Doc Destination Mismatch', sev: 'High', tol: 'Port consistency' },
  ];

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-900">
          System Configuration & Reviewer Settings
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Manage reviewer credentials, audit sign-off identities, deterministic tolerances, and engine policies.
        </p>
      </div>

      {/* Reviewer Identity Switcher */}
      <div className="card-subtle p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-blue-600" />
              <span>Active Reviewer Identity</span>
            </h3>
            <p className="text-xs text-slate-500">
              Select which authorized reviewer identity signs human determinations in the immutable audit trail.
            </p>
          </div>
          <span className="font-mono text-xs px-2.5 py-1 rounded bg-blue-50 text-blue-700 font-semibold border border-blue-200">
            Current: {currentReviewer.name}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {mockReviewers.map((rev) => {
            const isSelected = rev.id === currentReviewer.id;
            return (
              <div
                key={rev.id}
                onClick={() => handleSelectReviewer(rev)}
                className={`p-3.5 rounded-xl border cursor-pointer transition ${
                  isSelected
                    ? 'border-blue-500 bg-blue-50/40 ring-1 ring-blue-500 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300 bg-white'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-slate-900">{rev.name}</span>
                  {isSelected && (
                    <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
                  )}
                </div>
                <p className="text-[11px] text-slate-600 font-medium">{rev.role}</p>
                <p className="text-[10px] text-slate-400 font-mono mt-2 truncate">{rev.email}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Deterministic Verification Rules Registry */}
      <div className="card-subtle overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50/75 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-slate-600" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Deterministic Rule Engine & Tolerance Policies
            </h3>
          </div>
          <span className="text-[11px] text-slate-500">10 Active Validation Rules</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/50">
                <th className="table-th">Rule ID</th>
                <th className="table-th">Rule Name</th>
                <th className="table-th">Severity</th>
                <th className="table-th">Configured Tolerance / Math Precision</th>
                <th className="table-th">Enforcement</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rules.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/60">
                  <td className="table-td font-mono font-bold text-slate-900">{r.id}</td>
                  <td className="table-td font-medium text-slate-800">{r.name}</td>
                  <td className="table-td">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        r.sev === 'Critical'
                          ? 'bg-red-50 text-red-700 border border-red-200'
                          : r.sev === 'High'
                          ? 'bg-orange-50 text-orange-700 border border-orange-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}
                    >
                      {r.sev}
                    </span>
                  </td>
                  <td className="table-td font-mono text-slate-600">{r.tol}</td>
                  <td className="table-td text-emerald-700 font-semibold text-[11px]">
                    Deterministic
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Enterprise Policy & Governance Disclaimer */}
      <div className="card-subtle p-5 bg-gradient-to-r from-slate-50 via-white to-slate-50 border-slate-200 space-y-2">
        <div className="flex items-center gap-2 text-slate-900 font-bold text-xs uppercase tracking-wider">
          <Lock className="w-4 h-4 text-blue-600" />
          <span>Non-Autonomous Verification Governance (ISO / SOX Compliance)</span>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">
          The DocuVerify AI engine strictly operates under human-in-the-loop governance. AI agents perform optical character recognition, digital text extraction, schema canonicalization, and deterministic rule evaluation. Under no circumstances does the system alter commercial documents or autonomously approve or reject transactions. All review determinations require documented human justification written to an append-only audit trail.
        </p>
      </div>
    </div>
  );
};

