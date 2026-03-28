import { useState } from 'react';
import {
  Search, ChevronDown, ChevronRight, PlusCircle, Clock,
  CheckCircle2, XCircle, AlertCircle, FileText, TrendingUp,
  Stethoscope, IndianRupee, X
} from 'lucide-react';
import { getPatientCaseHistory, createEnhancement } from '../services/api';
import type { PatientCaseHistory, EnhancementResponse, EnhancementData } from '../types/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const STATUS_STYLES: Record<string, string> = {
  draft:     'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  submitted: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  approved:  'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  rejected:  'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  active:    'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
};

const STATUS_ICON: Record<string, React.ElementType> = {
  draft:     Clock,
  submitted: AlertCircle,
  approved:  CheckCircle2,
  rejected:  XCircle,
  active:    CheckCircle2,
};

function StatusBadge({ status }: { status: string }) {
  const Icon = STATUS_ICON[status] ?? Clock;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold capitalize ${STATUS_STYLES[status] ?? STATUS_STYLES.draft}`}>
      <Icon size={11} />
      {status}
    </span>
  );
}

function rupees(v?: number | null) {
  if (v == null) return '--';
  return `Rs. ${v.toLocaleString('en-IN')}`;
}

// ---------------------------------------------------------------------------
// Enhancement Form Modal
// ---------------------------------------------------------------------------
interface EnhancementFormProps {
  preAuthId: string;
  abhaId?: string;
  originalDiagnosis?: string;
  originalIcd10?: string;
  originalCost?: number;
  sequenceNo: number;
  onClose: () => void;
  onSaved: (e: EnhancementResponse) => void;
}

function EnhancementForm({
  preAuthId, abhaId, originalDiagnosis, originalIcd10, originalCost,
  sequenceNo, onClose, onSaved,
}: EnhancementFormProps) {
  const [form, setForm] = useState<Partial<EnhancementData>>({
    pre_auth_id: preAuthId,
    abha_id: abhaId,
    reason: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (key: keyof EnhancementData, val: string | number | undefined) =>
    setForm(f => ({ ...f, [key]: val }));

  const handleSubmit = async () => {
    if (!form.reason?.trim()) { setError('Reason for enhancement is required.'); return; }
    setSaving(true);
    setError(null);
    try {
      const result = await createEnhancement(preAuthId, form as EnhancementData);
      onSaved(result);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to submit enhancement.');
    } finally {
      setSaving(false);
    }
  };

  const Field = ({ label, field, type = 'text', area = false }: {
    label: string; field: keyof EnhancementData; type?: string; area?: boolean;
  }) => (
    <div>
      <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">{label}</label>
      {area ? (
        <textarea
          rows={3}
          value={(form[field] as string) ?? ''}
          onChange={e => set(field, e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
        />
      ) : (
        <input
          type={type}
          value={(form[field] as string | number) ?? ''}
          onChange={e => set(field, type === 'number' ? (e.target.value ? Number(e.target.value) : undefined) : e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
      )}
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 px-6 py-4 flex justify-between items-center rounded-t-2xl z-10">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Enhancement Request #{sequenceNo}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Update diagnosis or cost for this pre-authorization
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
            <X size={18} className="text-slate-500" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Original snapshot */}
          <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Original Pre-Auth Snapshot</p>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-slate-500 dark:text-slate-400">Diagnosis: </span>
                <span className="font-medium text-slate-800 dark:text-slate-200">{originalDiagnosis || '--'}</span>
              </div>
              <div>
                <span className="text-slate-500 dark:text-slate-400">ICD-10: </span>
                <span className="font-medium text-slate-800 dark:text-slate-200">{originalIcd10 || '--'}</span>
              </div>
              <div className="col-span-2">
                <span className="text-slate-500 dark:text-slate-400">Approved Amount: </span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400">{rupees(originalCost)}</span>
              </div>
            </div>
          </div>

          {/* Reason (required) */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
              Reason for Enhancement <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={2}
              value={form.reason ?? ''}
              onChange={e => set('reason', e.target.value)}
              placeholder="e.g. Patient developed migraine — updated diagnosis required"
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
            />
          </div>

          {/* Updated Diagnosis */}
          <div>
            <p className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <Stethoscope size={15} className="text-emerald-500" /> Updated Diagnosis
            </p>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Updated Diagnosis" field="updated_diagnosis" />
              <Field label="Updated ICD-10 Code" field="updated_icd10_code" />
              <Field label="Updated Line of Treatment" field="updated_line_of_treatment" />
              <Field label="Updated Surgery Name" field="updated_surgery_name" />
              <Field label="Updated ICD-10 PCS Code" field="updated_icd10_pcs_code" />
            </div>
          </div>

          {/* Clinical justification */}
          <Field label="Clinical Justification / Supporting Notes" field="clinical_justification" area />

          {/* Revised Costs */}
          <div>
            <p className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <IndianRupee size={15} className="text-emerald-500" /> Revised Cost Estimates (INR)
            </p>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Room Rent / Day" field="revised_room_rent_per_day" type="number" />
              <Field label="ICU Charges / Day" field="revised_icu_charges_per_day" type="number" />
              <Field label="OT Charges" field="revised_ot_charges" type="number" />
              <Field label="Surgeon Fees" field="revised_surgeon_fees" type="number" />
              <Field label="Medicines & Consumables" field="revised_medicines_consumables" type="number" />
              <Field label="Investigations" field="revised_investigations" type="number" />
            </div>
            <div className="mt-4 p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl border border-emerald-200 dark:border-emerald-800">
              <label className="block text-xs font-semibold text-emerald-700 dark:text-emerald-400 mb-1">
                Revised Total Estimated Cost (INR) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={(form.revised_total_estimated_cost as number) ?? ''}
                onChange={e => set('revised_total_estimated_cost', e.target.value ? Number(e.target.value) : undefined)}
                className="w-full px-3 py-2 rounded-lg border border-emerald-300 dark:border-emerald-700 bg-white dark:bg-slate-800 text-sm font-bold focus:outline-none focus:ring-2 focus:ring-emerald-500"
                placeholder="e.g. 150000"
              />
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 px-6 py-4 flex justify-end gap-3 rounded-b-2xl">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <PlusCircle size={15} />
            )}
            Submit Enhancement
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Enhancement history card (per pre-auth)
// ---------------------------------------------------------------------------
function EnhancementCard({ e }: { e: EnhancementResponse }) {
  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-4 bg-white dark:bg-slate-800/50">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold flex items-center justify-center">
            {e.sequence_no}
          </span>
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">Enhancement #{e.sequence_no}</span>
        </div>
        <StatusBadge status={e.status} />
      </div>

      <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
        <span className="font-semibold">Reason: </span>{e.reason}
      </p>

      <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs">
        {e.original_diagnosis && (
          <div className="col-span-2 pb-2 mb-1 border-b border-slate-100 dark:border-slate-700 grid grid-cols-2 gap-x-6">
            <div><span className="text-slate-400">Original Dx: </span><span className="text-slate-600 dark:text-slate-300">{e.original_diagnosis}</span></div>
            <div><span className="text-slate-400">Original ICD-10: </span><span className="text-slate-600 dark:text-slate-300">{e.original_icd10_code || '--'}</span></div>
          </div>
        )}
        {e.updated_diagnosis && (
          <div><span className="text-slate-400">Updated Dx: </span><span className="font-medium text-emerald-700 dark:text-emerald-400">{e.updated_diagnosis}</span></div>
        )}
        {e.updated_icd10_code && (
          <div><span className="text-slate-400">Updated ICD-10: </span><span className="font-medium text-slate-700 dark:text-slate-300">{e.updated_icd10_code}</span></div>
        )}
        {e.revised_total_estimated_cost != null && (
          <div className="col-span-2 mt-1">
            <span className="text-slate-400">Revised Total: </span>
            <span className="font-bold text-emerald-600 dark:text-emerald-400">{rupees(e.revised_total_estimated_cost)}</span>
            {e.original_total_cost != null && (
              <span className="text-slate-400 ml-2">
                (was {rupees(e.original_total_cost)},
                <span className={e.revised_total_estimated_cost > e.original_total_cost ? 'text-red-500' : 'text-emerald-500'}>
                  {' '}{e.revised_total_estimated_cost > e.original_total_cost ? '+' : ''}
                  {rupees(e.revised_total_estimated_cost - e.original_total_cost)}
                </span>)
              </span>
            )}
          </div>
        )}
      </div>

      {e.tpa_remarks && (
        <p className="mt-3 text-xs text-slate-500 dark:text-slate-400 italic border-t border-slate-100 dark:border-slate-700 pt-2">
          TPA Remarks: {e.tpa_remarks}
        </p>
      )}
      <p className="mt-2 text-xs text-slate-400">{e.created_at ? new Date(e.created_at).toLocaleString('en-IN') : ''}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Case row (one pre-auth + expandable enhancements + raise button)
// ---------------------------------------------------------------------------
function CaseRow({
  cas,
  onEnhancement,
}: {
  cas: PatientCaseHistory;
  onEnhancement: (cas: PatientCaseHistory) => void;
}) {
  const [open, setOpen] = useState(false);
  const ChevronIcon = open ? ChevronDown : ChevronRight;

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-2xl overflow-hidden">
      {/* Summary row */}
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full text-left px-5 py-4 flex items-start gap-4 hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors"
      >
        <ChevronIcon size={18} className="mt-0.5 text-slate-400 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap mb-1">
            <span className="font-semibold text-slate-900 dark:text-white text-sm truncate">
              {cas.provisional_diagnosis || 'No diagnosis'}
            </span>
            <StatusBadge status={cas.status} />
            {cas.enhancements.length > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300">
                <TrendingUp size={10} />
                {cas.enhancements.length} enhancement{cas.enhancements.length > 1 ? 's' : ''}
              </span>
            )}
          </div>
          <div className="flex gap-4 text-xs text-slate-500 dark:text-slate-400 flex-wrap">
            {cas.icd10_diagnosis_code && <span>ICD-10: {cas.icd10_diagnosis_code}</span>}
            {cas.hospital_name && <span>{cas.hospital_name}</span>}
            {cas.admission_date && <span>Admitted: {cas.admission_date}</span>}
            {cas.total_estimated_cost != null && (
              <span className="font-medium text-emerald-600 dark:text-emerald-400">
                {rupees(cas.total_estimated_cost)}
              </span>
            )}
          </div>
        </div>
        <div className="text-xs text-slate-400 shrink-0">
          {cas.created_at ? new Date(cas.created_at).toLocaleDateString('en-IN') : ''}
        </div>
      </button>

      {/* Expanded content */}
      {open && (
        <div className="px-5 pb-5 border-t border-slate-100 dark:border-slate-800">
          {/* Enhancement history */}
          {cas.enhancements.length > 0 ? (
            <div className="mt-4 space-y-3">
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Enhancement History</p>
              {cas.enhancements.map(e => <EnhancementCard key={e.id} e={e} />)}
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-400 dark:text-slate-500 italic">No enhancements raised yet.</p>
          )}

          {/* Raise new enhancement */}
          <button
            onClick={() => onEnhancement(cas)}
            className="mt-4 flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition-colors"
          >
            <PlusCircle size={15} />
            Raise Enhancement #{cas.enhancements.length + 1}
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
export default function EnhancementPage() {
  const [abhaInput, setAbhaInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cases, setCases] = useState<PatientCaseHistory[] | null>(null);

  const [formTarget, setFormTarget] = useState<PatientCaseHistory | null>(null);

  const handleSearch = async () => {
    const id = abhaInput.trim();
    if (!id) return;
    setLoading(true);
    setError(null);
    setCases(null);
    try {
      const data = await getPatientCaseHistory(id);
      setCases(data);
      if (data.length === 0) setError('No pre-authorization records found for this ABHA ID.');
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to fetch patient history.');
    } finally {
      setLoading(false);
    }
  };

  const handleEnhancementSaved = (saved: EnhancementResponse, preAuthId: string) => {
    setCases(prev =>
      (prev ?? []).map(c =>
        c.pre_auth_id === preAuthId
          ? { ...c, enhancements: [...c.enhancements, saved] }
          : c
      )
    );
    setFormTarget(null);
  };

  const patientName = cases?.[0]?.patient_name;
  const abhaId = cases?.[0]?.abha_id;

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">Enhancement Requests</h1>
        <p className="mt-1 text-slate-500 dark:text-slate-400">
          Search a patient by ABHA ID to view their diagnosis history and raise enhancement requests.
        </p>
      </div>

      {/* Search bar */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-700 p-6">
        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
          Enter ABHA ID
        </label>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={abhaInput}
              onChange={e => setAbhaInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="e.g. 12-3456-7890-1234"
              className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading || !abhaInput.trim()}
            className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Search size={15} />
            )}
            Search
          </button>
        </div>

        {/* Quick ABHA hints */}
        <div className="mt-3 flex flex-wrap gap-2">
          {[
            '12-3456-7890-1234',
            '14-2345-6789-0011',
            '18-9876-5432-1001',
            '21-1111-2222-3333',
            '31-4444-5555-6666',
          ].map(id => (
            <button
              key={id}
              onClick={() => { setAbhaInput(id); }}
              className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors font-mono"
            >
              {id}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {cases !== null && cases.length > 0 && (
        <div className="space-y-4">
          {/* Patient banner */}
          <div className="flex items-center gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl px-6 py-4">
            <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
              <FileText size={18} className="text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="font-bold text-slate-900 dark:text-white">{patientName || 'Patient'}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">ABHA ID: {abhaId} &bull; {cases.length} pre-auth record{cases.length > 1 ? 's' : ''}</p>
            </div>
          </div>

          {/* Case list */}
          <p className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide px-1">
            Diagnosis History
          </p>
          <div className="space-y-3">
            {cases.map(c => (
              <CaseRow
                key={c.pre_auth_id}
                cas={c}
                onEnhancement={setFormTarget}
              />
            ))}
          </div>
        </div>
      )}

      {/* Enhancement form modal */}
      {formTarget && (
        <EnhancementForm
          preAuthId={formTarget.pre_auth_id}
          abhaId={formTarget.abha_id}
          originalDiagnosis={formTarget.provisional_diagnosis}
          originalIcd10={formTarget.icd10_diagnosis_code}
          originalCost={formTarget.total_estimated_cost}
          sequenceNo={formTarget.enhancements.length + 1}
          onClose={() => setFormTarget(null)}
          onSaved={saved => handleEnhancementSaved(saved, formTarget.pre_auth_id)}
        />
      )}
    </div>
  );
}
