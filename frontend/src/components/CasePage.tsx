import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ChevronDown, ChevronUp, Upload, CheckCircle2, AlertTriangle,
  AlertCircle, Download, Plus, ArrowLeft, IndianRupee, FileText,
} from 'lucide-react';
import {
  getCase, generatePreAuthPdf, createEnhancement,
  createDischarge, extractDischargeData, updateDischarge,
  createSettlement, updateSettlement,
} from '../services/api';
import type {
  CaseDetail, EnhancementData, DischargeData, DischargeResponse,
  SettlementResponse,
} from '../types/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt(n: number | undefined | null) {
  if (n == null) return '—';
  return `₹${n.toLocaleString('en-IN')}`;
}

function Spinner({ sm }: { sm?: boolean }) {
  return (
    <span
      className={`inline-block rounded-full border-2 border-white/30 border-t-white animate-spin ${
        sm ? 'w-3.5 h-3.5' : 'w-4 h-4'
      }`}
    />
  );
}

function Badge({ status }: { status: string }) {
  const map: Record<string, string> = {
    draft: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400',
    submitted: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400',
    pending: 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400',
    approved: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400',
    rejected: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400',
    paid: 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-400',
  };
  return (
    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${map[status] ?? map.pending}`}>
      {status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Step 1 — Pre-Auth
// ---------------------------------------------------------------------------

function PreAuthPanel({ caseData }: { caseData: CaseDetail }) {
  const [open, setOpen] = useState(true);
  const [generating, setGenerating] = useState(false);
  const pa = caseData.pre_auth;

  const handleGeneratePdf = async () => {
    if (!pa) return;
    setGenerating(true);
    try {
      const blob = await generatePreAuthPdf(pa.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `pre_auth_${pa.id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setGenerating(false);
    }
  };

  if (!pa) return null;

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-full bg-emerald-500 flex items-center justify-center text-white text-xs font-bold">1</div>
          <span className="font-semibold text-slate-900 dark:text-white">Pre-Authorization</span>
          <Badge status={pa.status} />
        </div>
        {open ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
      </button>

      {open && (
        <div className="px-6 pb-6 border-t border-slate-100 dark:border-slate-800">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4 text-sm">
            <Info label="Patient" value={pa.patient_name} />
            <Info label="ABHA ID" value={pa.abha_id} />
            <Info label="Hospital" value={pa.hospital_name} />
            <Info label="Diagnosis" value={pa.provisional_diagnosis} />
            <Info label="ICD-10" value={pa.icd10_diagnosis_code} />
            <Info label="Admission Date" value={pa.admission_date} />
            <Info label="Admission Type" value={pa.admission_type} />
            <Info label="Doctor" value={pa.doctor_name} />
            <Info label="Total Estimated Cost" value={fmt(pa.total_estimated_cost)} />
          </div>
          <div className="mt-5 flex items-center gap-3 flex-wrap">
            <button
              onClick={handleGeneratePdf}
              disabled={generating}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-xl transition-colors disabled:opacity-60"
            >
              {generating ? <Spinner sm /> : <Download size={14} />}
              Generate PDF
            </button>
            {pa.patient_id && (
              <Link
                to={`/patients/${pa.patient_id}`}
                className="flex items-center gap-2 px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 text-sm font-semibold rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                <FileText size={14} />
                View Patient Record
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-xs text-slate-400 dark:text-slate-500 mb-0.5">{label}</p>
      <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{value || '—'}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 2 — Enhancement
// ---------------------------------------------------------------------------

function EnhancementPanel({ caseData, onRefresh }: { caseData: CaseDetail; onRefresh: () => void }) {
  const [open, setOpen] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<Partial<EnhancementData>>({});
  const [err, setErr] = useState<string | null>(null);

  const pa = caseData.pre_auth;
  const enhancements = caseData.enhancements || [];

  const set = (k: keyof EnhancementData, v: unknown) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    if (!pa) return;
    if (!form.reason?.trim()) { setErr('Reason is required'); return; }
    setSaving(true); setErr(null);
    try {
      await createEnhancement(pa.id, { ...form, pre_auth_id: pa.id, reason: form.reason! });
      setShowForm(false);
      setForm({});
      onRefresh();
    } catch (e: any) {
      setErr(e.response?.data?.detail || e.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold ${enhancements.length > 0 ? 'bg-emerald-500' : 'bg-slate-400 dark:bg-slate-600'}`}>2</div>
          <span className="font-semibold text-slate-900 dark:text-white">Enhancement</span>
          {enhancements.length > 0 && (
            <span className="text-xs bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 px-2 py-0.5 rounded-full font-medium">
              {enhancements.length} enhancement{enhancements.length > 1 ? 's' : ''}
            </span>
          )}
        </div>
        {open ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
      </button>

      {open && (
        <div className="px-6 pb-6 border-t border-slate-100 dark:border-slate-800">
          {enhancements.length === 0 && !showForm && (
            <p className="text-sm text-slate-400 mt-4">No enhancements yet.</p>
          )}

          {enhancements.map((e) => (
            <div key={e.id} className="mt-4 p-4 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-sm">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-bold text-slate-500 dark:text-slate-400">#{e.sequence_no}</span>
                <Badge status={e.status} />
              </div>
              <p className="font-medium text-slate-800 dark:text-slate-200 mb-1">{e.reason}</p>
              {e.clinical_justification && <p className="text-slate-500 dark:text-slate-400 text-xs">{e.clinical_justification}</p>}
              <div className="grid grid-cols-2 gap-2 mt-2">
                {e.updated_diagnosis && <Info label="Updated Diagnosis" value={e.updated_diagnosis} />}
                {e.revised_total_estimated_cost != null && (
                  <Info label="Revised Cost" value={fmt(e.revised_total_estimated_cost)} />
                )}
              </div>
            </div>
          ))}

          {showForm && (
            <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
              <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">New Enhancement</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <FormInput label="Reason *" value={form.reason || ''} onChange={(v) => set('reason', v)} span2 />
                <FormInput label="Clinical Justification" value={form.clinical_justification || ''} onChange={(v) => set('clinical_justification', v)} span2 area />
                <FormInput label="Updated Diagnosis" value={form.updated_diagnosis || ''} onChange={(v) => set('updated_diagnosis', v)} />
                <FormInput label="Updated ICD-10 Code" value={form.updated_icd10_code || ''} onChange={(v) => set('updated_icd10_code', v)} />
                <FormInput label="Revised Total Cost (₹)" value={form.revised_total_estimated_cost?.toString() || ''} onChange={(v) => set('revised_total_estimated_cost', v ? Number(v) : undefined)} type="number" />
              </div>
              {err && <p className="text-xs text-red-500 mt-2">{err}</p>}
              <div className="flex gap-2 mt-3">
                <button onClick={handleSubmit} disabled={saving}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-60 flex items-center gap-2">
                  {saving ? <Spinner sm /> : null} Save
                </button>
                <button onClick={() => { setShowForm(false); setErr(null); }}
                  className="px-4 py-1.5 border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-400 text-sm rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
                  Cancel
                </button>
              </div>
            </div>
          )}

          {!showForm && (
            <button onClick={() => setShowForm(true)}
              className="mt-4 flex items-center gap-2 text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:underline">
              <Plus size={15} /> Add Enhancement
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function FormInput({
  label, value, onChange, type = 'text', area = false, span2 = false,
}: {
  label: string; value: string; onChange: (v: string) => void;
  type?: string; area?: boolean; span2?: boolean;
}) {
  const cls = 'w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-colors';
  return (
    <div className={span2 ? 'col-span-2' : ''}>
      <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">{label}</label>
      {area ? (
        <textarea rows={3} value={value} onChange={(e) => onChange(e.target.value)} className={cls + ' resize-none'} />
      ) : (
        <input type={type} value={value} onChange={(e) => onChange(e.target.value)} className={cls} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 3 — Discharge
// ---------------------------------------------------------------------------

type DischargeFormState = Partial<DischargeData>;

function DischargePanel({
  caseData, discharge, onRefresh,
}: {
  caseData: CaseDetail;
  discharge: DischargeResponse | null;
  onRefresh: () => void;
}) {
  const [open, setOpen] = useState(true);
  const [editing, setEditing] = useState(!discharge);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dischargeId, setDischargeId] = useState<string | null>(discharge?.id ?? null);
  const [form, setForm] = useState<DischargeFormState>(discharge ?? {});
  const [err, setErr] = useState<string | null>(null);

  const pa = caseData.pre_auth;

  const set = (k: keyof DischargeFormState, v: unknown) => setForm((f) => ({ ...f, [k]: v }));

  const handleFileUpload = async (file: File) => {
    if (!pa) return;
    setUploading(true); setErr(null);
    try {
      let id = dischargeId;
      if (!id) {
        const created = await createDischarge({
          bill_no: caseData.bill_no,
          pre_auth_id: pa.id,
          abha_id: pa.abha_id ?? undefined,
        });
        id = created.id;
        setDischargeId(id);
      }
      const extracted = await extractDischargeData(id!, file);
      setForm((f) => ({
        ...f,
        discharge_date: extracted.discharge_date ?? f.discharge_date,
        final_diagnosis: extracted.final_diagnosis ?? f.final_diagnosis,
        final_icd10_codes: extracted.final_icd10_codes ?? f.final_icd10_codes,
        procedure_codes: extracted.procedure_codes ?? f.procedure_codes,
        room_charges: extracted.room_charges ?? f.room_charges,
        icu_charges: extracted.icu_charges ?? f.icu_charges,
        surgery_charges: extracted.surgery_charges ?? f.surgery_charges,
        medicine_charges: extracted.medicine_charges ?? f.medicine_charges,
        investigation_charges: extracted.investigation_charges ?? f.investigation_charges,
        other_charges: extracted.other_charges ?? f.other_charges,
        total_bill_amount: extracted.total_bill_amount ?? f.total_bill_amount,
      }));
    } catch (e: any) {
      setErr(e.response?.data?.detail || e.message || 'Extraction failed');
    } finally {
      setUploading(false);
    }
  };

  const handleSave = async () => {
    if (!pa) return;
    setSaving(true); setErr(null);
    try {
      let id = dischargeId;
      if (!id) {
        const created = await createDischarge({
          bill_no: caseData.bill_no,
          pre_auth_id: pa.id,
          abha_id: pa.abha_id ?? undefined,
          ...form,
        });
        setDischargeId(created.id);
      } else {
        await updateDischarge(id, {
          bill_no: caseData.bill_no,
          pre_auth_id: pa.id,
          ...form,
        });
      }
      setEditing(false);
      onRefresh();
    } catch (e: any) {
      setErr(e.response?.data?.detail || e.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const currentDischarge = discharge;

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold ${currentDischarge ? 'bg-emerald-500' : 'bg-slate-400 dark:bg-slate-600'}`}>3</div>
          <span className="font-semibold text-slate-900 dark:text-white">Discharge</span>
          {currentDischarge && <Badge status={currentDischarge.status || 'pending'} />}
        </div>
        {open ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
      </button>

      {open && (
        <div className="px-6 pb-6 border-t border-slate-100 dark:border-slate-800">
          {/* Revenue flags */}
          {currentDischarge && !editing && currentDischarge.revenue_flags?.length > 0 && (
            <div className="mt-4 space-y-2">
              {currentDischarge.revenue_flags.map((flag, i) => (
                <div key={i} className={`flex items-start gap-2 px-4 py-3 rounded-xl text-sm ${
                  flag.severity === 'critical'
                    ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400'
                    : 'bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400'
                }`}>
                  {flag.severity === 'critical'
                    ? <AlertCircle size={16} className="shrink-0 mt-0.5" />
                    : <AlertTriangle size={16} className="shrink-0 mt-0.5" />}
                  <span>{flag.message}</span>
                </div>
              ))}
            </div>
          )}

          {/* Existing discharge summary (read mode) */}
          {currentDischarge && !editing && (
            <div className="mt-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                <Info label="Discharge Date" value={currentDischarge.discharge_date} />
                <Info label="Final Diagnosis" value={currentDischarge.final_diagnosis} />
                <Info label="ICD-10 Codes" value={currentDischarge.final_icd10_codes} />
                <Info label="Procedure Codes" value={currentDischarge.procedure_codes} />
                <Info label="Room Charges" value={fmt(currentDischarge.room_charges)} />
                <Info label="ICU Charges" value={fmt(currentDischarge.icu_charges)} />
                <Info label="Surgery Charges" value={fmt(currentDischarge.surgery_charges)} />
                <Info label="Medicine Charges" value={fmt(currentDischarge.medicine_charges)} />
                <Info label="Investigation Charges" value={fmt(currentDischarge.investigation_charges)} />
                <Info label="Other Charges" value={fmt(currentDischarge.other_charges)} />
                <Info label="Total Bill Amount" value={fmt(currentDischarge.total_bill_amount)} />
              </div>
              <button onClick={() => setEditing(true)}
                className="mt-4 text-sm text-emerald-600 dark:text-emerald-400 hover:underline font-medium">
                Edit / Re-upload
              </button>
            </div>
          )}

          {/* Upload + form (edit mode) */}
          {editing && (
            <div className="mt-4">
              {/* File upload area */}
              <label className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-6 cursor-pointer transition-colors ${
                uploading
                  ? 'border-emerald-400 bg-emerald-50 dark:bg-emerald-900/10'
                  : 'border-slate-300 dark:border-slate-600 hover:border-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/10'
              }`}>
                <input type="file" accept=".pdf" className="hidden"
                  disabled={uploading}
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileUpload(f); }} />
                {uploading ? (
                  <>
                    <div className="w-8 h-8 border-4 border-emerald-200 border-t-emerald-500 rounded-full animate-spin mb-2" />
                    <p className="text-sm text-emerald-600 dark:text-emerald-400 font-medium">Extracting with Gemini...</p>
                  </>
                ) : (
                  <>
                    <Upload size={22} className="text-slate-400 mb-2" />
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Upload Discharge Summary PDF</p>
                    <p className="text-xs text-slate-400 mt-1">Gemini will auto-fill the fields below</p>
                  </>
                )}
              </label>

              {/* Editable fields */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
                <FormInput label="Discharge Date" value={form.discharge_date || ''} onChange={(v) => set('discharge_date', v)} type="date" />
                <FormInput label="Final Diagnosis" value={form.final_diagnosis || ''} onChange={(v) => set('final_diagnosis', v)} />
                <FormInput label="ICD-10 Codes" value={form.final_icd10_codes || ''} onChange={(v) => set('final_icd10_codes', v)} />
                <FormInput label="Procedure Codes (ICD-10 PCS/CPT)" value={form.procedure_codes || ''} onChange={(v) => set('procedure_codes', v)} />
                <FormInput label="Room Charges (₹)" value={form.room_charges?.toString() || ''} onChange={(v) => set('room_charges', v ? Number(v) : undefined)} type="number" />
                <FormInput label="ICU Charges (₹)" value={form.icu_charges?.toString() || ''} onChange={(v) => set('icu_charges', v ? Number(v) : undefined)} type="number" />
                <FormInput label="Surgery Charges (₹)" value={form.surgery_charges?.toString() || ''} onChange={(v) => set('surgery_charges', v ? Number(v) : undefined)} type="number" />
                <FormInput label="Medicine Charges (₹)" value={form.medicine_charges?.toString() || ''} onChange={(v) => set('medicine_charges', v ? Number(v) : undefined)} type="number" />
                <FormInput label="Investigation Charges (₹)" value={form.investigation_charges?.toString() || ''} onChange={(v) => set('investigation_charges', v ? Number(v) : undefined)} type="number" />
                <FormInput label="Other Charges (₹)" value={form.other_charges?.toString() || ''} onChange={(v) => set('other_charges', v ? Number(v) : undefined)} type="number" />
                <FormInput label="Total Bill Amount (₹)" value={form.total_bill_amount?.toString() || ''} onChange={(v) => set('total_bill_amount', v ? Number(v) : undefined)} type="number" />
              </div>

              {err && <p className="text-xs text-red-500 mt-2">{err}</p>}

              <div className="flex gap-2 mt-4">
                <button onClick={handleSave} disabled={saving}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-xl transition-colors disabled:opacity-60 flex items-center gap-2">
                  {saving ? <Spinner sm /> : null} Save Discharge
                </button>
                {currentDischarge && (
                  <button onClick={() => { setEditing(false); setErr(null); }}
                    className="px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-400 text-sm rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
                    Cancel
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 4 — Settlement
// ---------------------------------------------------------------------------

function SettlementPanel({
  caseData, discharge, settlement, onRefresh,
}: {
  caseData: CaseDetail;
  discharge: DischargeResponse | null;
  settlement: SettlementResponse | null;
  onRefresh: () => void;
}) {
  const [open, setOpen] = useState(true);
  const [deduction, setDeduction] = useState(settlement?.deduction_amount?.toString() || '0');
  const [deductionReason, setDeductionReason] = useState(settlement?.deduction_reason || '');
  const [tpaRemarks, setTpaRemarks] = useState(settlement?.tpa_remarks || '');
  const [settlementDate, setSettlementDate] = useState(settlement?.settlement_date || '');
  const [saving, setSaving] = useState(false);
  const [statusLoading, setStatusLoading] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const pa = caseData.pre_auth;

  const preAuthEstimate = pa?.total_estimated_cost ?? null;
  const claimedAmount = discharge?.total_bill_amount ?? null;
  const deductionNum = parseFloat(deduction) || 0;
  const finalAmount = claimedAmount != null ? Math.max(0, claimedAmount - deductionNum) : null;
  const variance = preAuthEstimate != null && claimedAmount != null ? claimedAmount - preAuthEstimate : null;

  const handleCreate = async () => {
    if (!pa) return;
    setSaving(true); setErr(null);
    try {
      await createSettlement({
        bill_no: caseData.bill_no,
        pre_auth_id: pa.id,
        discharge_id: discharge?.id,
        abha_id: pa.abha_id ?? undefined,
        deduction_amount: deductionNum,
        deduction_reason: deductionReason || undefined,
        tpa_remarks: tpaRemarks || undefined,
        settlement_date: settlementDate || undefined,
      });
      onRefresh();
    } catch (e: any) {
      setErr(e.response?.data?.detail || e.message || 'Failed to create settlement');
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    if (!settlement) return;
    setStatusLoading(newStatus); setErr(null);
    try {
      await updateSettlement(settlement.id, {
        bill_no: caseData.bill_no,
        status: newStatus,
        deduction_amount: parseFloat(deduction) || 0,
        deduction_reason: deductionReason || undefined,
        tpa_remarks: tpaRemarks || undefined,
        settlement_date: settlementDate || undefined,
      });
      onRefresh();
    } catch (e: any) {
      setErr(e.response?.data?.detail || e.message || 'Update failed');
    } finally {
      setStatusLoading(null);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold ${settlement ? 'bg-emerald-500' : 'bg-slate-400 dark:bg-slate-600'}`}>4</div>
          <span className="font-semibold text-slate-900 dark:text-white">Settlement</span>
          {settlement && <Badge status={settlement.status || 'pending'} />}
        </div>
        {open ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
      </button>

      {open && (
        <div className="px-6 pb-6 border-t border-slate-100 dark:border-slate-800">
          {!discharge ? (
            <div className="flex items-center gap-2 mt-4 text-sm text-amber-600 dark:text-amber-400">
              <AlertTriangle size={16} />
              Complete Discharge first before creating a settlement.
            </div>
          ) : (
            <>
              {/* Comparison table */}
              <div className="mt-4 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden text-sm">
                <table className="w-full">
                  <tbody>
                    <tr className="border-b border-slate-100 dark:border-slate-800">
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400">Pre-Auth Estimate</td>
                      <td className="px-4 py-3 font-semibold text-slate-800 dark:text-slate-200 text-right">{fmt(preAuthEstimate)}</td>
                    </tr>
                    <tr className="border-b border-slate-100 dark:border-slate-800">
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400">Final Bill (Claimed)</td>
                      <td className="px-4 py-3 font-semibold text-slate-800 dark:text-slate-200 text-right">{fmt(claimedAmount)}</td>
                    </tr>
                    {variance != null && (
                      <tr className="border-b border-slate-100 dark:border-slate-800">
                        <td className="px-4 py-3 text-slate-500 dark:text-slate-400">Variance</td>
                        <td className={`px-4 py-3 font-semibold text-right ${variance > 0 ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                          {variance > 0 ? '+' : ''}{fmt(variance)}
                        </td>
                      </tr>
                    )}
                    <tr>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400">Final Settlement</td>
                      <td className="px-4 py-3 font-bold text-emerald-700 dark:text-emerald-400 text-right text-base">{fmt(settlement?.final_settlement_amount ?? finalAmount)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Editable fields */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
                <FormInput label="Deduction Amount (₹)" value={deduction} onChange={setDeduction} type="number" />
                <FormInput label="Deduction Reason" value={deductionReason} onChange={setDeductionReason} />
                <FormInput label="TPA Remarks" value={tpaRemarks} onChange={setTpaRemarks} span2 area />
                <FormInput label="Settlement Date" value={settlementDate} onChange={setSettlementDate} type="date" />
              </div>

              {err && <p className="text-xs text-red-500 mt-2">{err}</p>}

              {/* Actions */}
              {!settlement ? (
                <button onClick={handleCreate} disabled={saving}
                  className="mt-4 flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-xl transition-colors disabled:opacity-60">
                  {saving ? <Spinner sm /> : <IndianRupee size={14} />}
                  Create Settlement
                </button>
              ) : (
                <div className="mt-4 flex flex-wrap gap-2">
                  {(['approved', 'rejected', 'paid'] as const).map((s) => {
                    const labels: Record<string, string> = { approved: 'Approve', rejected: 'Reject', paid: 'Mark Paid' };
                    const colors: Record<string, string> = {
                      approved: 'bg-emerald-600 hover:bg-emerald-700',
                      rejected: 'bg-red-600 hover:bg-red-700',
                      paid: 'bg-purple-600 hover:bg-purple-700',
                    };
                    return (
                      <button key={s} onClick={() => handleStatusChange(s)}
                        disabled={statusLoading !== null || settlement.status === s}
                        className={`flex items-center gap-1.5 px-4 py-2 text-white text-sm font-semibold rounded-xl transition-colors disabled:opacity-50 ${colors[s]}`}>
                        {statusLoading === s ? <Spinner sm /> : null}
                        {labels[s]}
                      </button>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stepper
// ---------------------------------------------------------------------------

function Stepper({ caseData }: { caseData: CaseDetail }) {
  const steps = [
    { label: 'Pre-Auth', done: true },
    { label: 'Enhancement', done: caseData.enhancements.length > 0 },
    { label: 'Discharge', done: !!caseData.discharge },
    { label: 'Settlement', done: !!caseData.settlement },
  ];

  return (
    <div className="flex items-center gap-0 mb-8">
      {steps.map((s, i) => (
        <div key={s.label} className="flex items-center">
          <div className="flex flex-col items-center">
            <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-sm transition-colors ${
              s.done ? 'bg-emerald-500 shadow-emerald-200 dark:shadow-emerald-900' : 'bg-slate-300 dark:bg-slate-700'
            }`}>
              {s.done ? <CheckCircle2 size={18} /> : i + 1}
            </div>
            <span className="text-xs mt-1 text-slate-500 dark:text-slate-400 hidden sm:block whitespace-nowrap">{s.label}</span>
          </div>
          {i < steps.length - 1 && (
            <div className={`h-0.5 w-12 sm:w-20 mx-1 transition-colors ${
              steps[i + 1].done ? 'bg-emerald-400' : 'bg-slate-200 dark:bg-slate-700'
            }`} />
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main CasePage
// ---------------------------------------------------------------------------

export default function CasePage() {
  const { billNo } = useParams<{ billNo: string }>();
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!billNo) return;
    setLoading(true); setError(null);
    try {
      const data = await getCase(decodeURIComponent(billNo));
      setCaseData(data);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Failed to load case');
    } finally {
      setLoading(false);
    }
  }, [billNo]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-10 h-10 border-4 border-emerald-200 border-t-emerald-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="p-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl text-red-700 dark:text-red-400">
        <p className="font-semibold">{error || 'Case not found'}</p>
        <Link to="/cases" className="text-sm underline mt-2 inline-block">Back to Cases</Link>
      </div>
    );
  }

  const pa = caseData.pre_auth;

  return (
    <div>
      {/* Back link */}
      <Link to="/cases" className="inline-flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white mb-6 transition-colors">
        <ArrowLeft size={15} /> All Cases
      </Link>

      {/* Case header */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm px-6 py-5 mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <FileText size={16} className="text-emerald-500" />
              <span className="font-mono text-sm bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded-lg">
                {caseData.bill_no}
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">
              {pa?.patient_name || 'Unknown Patient'}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              {pa?.hospital_name || ''}
              {pa?.hospital_name && pa?.admission_date ? ' · ' : ''}
              {pa?.admission_date || ''}
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            {pa && <Badge status={pa.status} />}
          </div>
        </div>
      </div>

      {/* Stepper */}
      <Stepper caseData={caseData} />

      {/* Step panels */}
      <div className="space-y-4">
        <PreAuthPanel caseData={caseData} />
        <EnhancementPanel caseData={caseData} onRefresh={load} />
        <DischargePanel
          caseData={caseData}
          discharge={caseData.discharge}
          onRefresh={load}
        />
        <SettlementPanel
          caseData={caseData}
          discharge={caseData.discharge}
          settlement={caseData.settlement}
          onRefresh={load}
        />
      </div>
    </div>
  );
}
