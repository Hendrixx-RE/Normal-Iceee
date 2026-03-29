import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload, FileText, CheckCircle2, XCircle, Clock, Image,
  FileSpreadsheet, Sheet, Plus, Play, RotateCcw,
  ShieldCheck, ScanText, CaseSensitive, BarChart2, Brain, Hospital, BadgeCheck, Zap,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type FileStatus = 'queued' | 'processing' | 'done' | 'error';

export interface QueueItem {
  id: string;
  file: File;
  status: FileStatus;
  error?: string;
}

interface FileUploadProps {
  onFileSelect: (file: File) => Promise<void>;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ACCEPTED_EXTENSIONS = new Set([
  '.pdf', '.jpg', '.jpeg', '.png', '.webp', '.tiff', '.tif', '.bmp',
  '.docx', '.xlsx', '.xls', '.csv',
]);

const PIPELINE_STEPS = [
  { label: 'Validating document',         Icon: ShieldCheck,   target: 8,  msPerPercent: 80  },
  { label: 'Reading document structure',  Icon: ScanText,      target: 20, msPerPercent: 150 },
  { label: 'Extracting text content',     Icon: CaseSensitive, target: 42, msPerPercent: 220 },
  { label: 'Assessing content quality',   Icon: BarChart2,     target: 52, msPerPercent: 130 },
  { label: 'NLP + LLM clinical analysis', Icon: Brain,         target: 78, msPerPercent: 380 },
  { label: 'Mapping to FHIR R4 standard', Icon: Hospital,      target: 90, msPerPercent: 260 },
  { label: 'Running billing validation',  Icon: BadgeCheck,    target: 97, msPerPercent: 200 },
  { label: 'Finalising results',          Icon: Zap,           target: 99, msPerPercent: 1800 },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function isAccepted(file: File): boolean {
  const ext = '.' + (file.name.split('.').pop()?.toLowerCase() ?? '');
  return ACCEPTED_EXTENSIONS.has(ext);
}

function getFileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() ?? '';
  if (['jpg', 'jpeg', 'png', 'webp', 'tiff', 'tif', 'bmp'].includes(ext)) return Image;
  if (['xlsx', 'xls'].includes(ext)) return FileSpreadsheet;
  if (ext === 'csv') return Sheet;
  return FileText;
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect }) => {
  const navigate = useNavigate();
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [allDone, setAllDone] = useState(false);

  // Progress animation state (for the currently-active file)
  const [progress, setProgress] = useState(0);
  const [stepIndex, setStepIndex] = useState(0);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const intervalRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const progressRef = useRef(0);
  const stepIndexRef = useRef(0);

  // ── Progress animation helpers ──────────────────────────────────────────

  const clearTick = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const resetProgress = useCallback(() => {
    clearTick();
    progressRef.current = 0;
    stepIndexRef.current = 0;
    setProgress(0);
    setStepIndex(0);
  }, [clearTick]);

  const startTicking = useCallback(() => {
    clearTick();
    const tick = () => {
      const step = PIPELINE_STEPS[stepIndexRef.current];
      if (!step) return;
      const next = progressRef.current + 1;
      if (next >= step.target) {
        progressRef.current = step.target;
        setProgress(step.target);
        if (stepIndexRef.current < PIPELINE_STEPS.length - 1) {
          stepIndexRef.current += 1;
          setStepIndex(stepIndexRef.current);
          clearTick();
          intervalRef.current = setInterval(tick, PIPELINE_STEPS[stepIndexRef.current].msPerPercent);
        } else {
          clearTick();
        }
      } else {
        progressRef.current = next;
        setProgress(next);
      }
    };
    intervalRef.current = setInterval(tick, PIPELINE_STEPS[stepIndexRef.current].msPerPercent);
  }, [clearTick]);

  // ── File handling ────────────────────────────────────────────────────────

  const addFiles = useCallback((files: FileList | File[]) => {
    const valid: QueueItem[] = [];
    const rejected: string[] = [];
    Array.from(files).forEach(f => {
      if (isAccepted(f)) {
        valid.push({ id: uid(), file: f, status: 'queued' });
      } else {
        rejected.push(f.name);
      }
    });
    if (rejected.length) {
      alert(`Skipped unsupported file(s):\n${rejected.join('\n')}\n\nAccepted: PDF, JPG, PNG, WEBP, TIFF, DOCX, XLSX, XLS, CSV`);
    }
    if (valid.length) {
      setQueue(prev => [...prev, ...valid]);
      setAllDone(false);
    }
  }, []);

  const removeFile = (id: string) => {
    setQueue(prev => prev.filter(q => q.id !== id));
  };

  // ── Queue processor (sequential) ────────────────────────────────────────

  const runQueue = useCallback(async (items: QueueItem[]) => {
    setIsRunning(true);
    setAllDone(false);

    for (const item of items) {
      if (item.status !== 'queued') continue;

      setActiveId(item.id);
      setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'processing' } : q));
      resetProgress();
      startTicking();

      try {
        await onFileSelect(item.file);
        clearTick();
        setProgress(100);
        await new Promise(r => setTimeout(r, 300)); // brief pause so user sees 100%
        setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'done' } : q));
      } catch (err: any) {
        clearTick();
        setQueue(prev => prev.map(q =>
          q.id === item.id
            ? { ...q, status: 'error', error: err.message || 'Processing failed' }
            : q
        ));
      }
    }

    setIsRunning(false);
    setActiveId(null);
    setAllDone(true);
  }, [onFileSelect, resetProgress, startTicking, clearTick]);

  const handleStart = () => {
    const queued = queue.filter(q => q.status === 'queued');
    if (queued.length) runQueue(queued);
  };

  const handleReset = () => {
    clearTick();
    setQueue([]);
    setIsRunning(false);
    setActiveId(null);
    setAllDone(false);
    resetProgress();
  };

  // ── Drag-and-drop ────────────────────────────────────────────────────────

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isRunning) setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (!isRunning && e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      addFiles(e.target.files);
      e.target.value = '';
    }
  };

  // ── Derived counts ───────────────────────────────────────────────────────

  const doneCount  = queue.filter(q => q.status === 'done').length;
  const errorCount = queue.filter(q => q.status === 'error').length;
  const queuedCount = queue.filter(q => q.status === 'queued').length;
  const activeItem = queue.find(q => q.id === activeId);
  const currentStep = PIPELINE_STEPS[Math.min(stepIndex, PIPELINE_STEPS.length - 1)];

  // ── Empty state: drop zone only ─────────────────────────────────────────
  if (queue.length === 0) {
    return (
      <label
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-3xl p-20 flex flex-col items-center justify-center bg-white dark:bg-slate-800 transition-all cursor-pointer group w-full ${
          dragActive
            ? 'border-blue-500 bg-blue-50/30 dark:bg-blue-900/10'
            : 'border-slate-300 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-500 hover:bg-blue-50/30 dark:hover:bg-blue-900/10'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleInputChange}
          accept=".pdf,.jpg,.jpeg,.png,.webp,.tiff,.tif,.bmp,.docx,.xlsx,.xls,.csv"
        />
        <div className="bg-blue-100 dark:bg-blue-900/50 p-6 rounded-full text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform mb-6">
          <Upload size={48} />
        </div>
        <h3 className="text-xl font-semibold mb-2 text-slate-900 dark:text-white">
          Drop Clinical Documents Here
        </h3>
        <p className="text-slate-400 dark:text-slate-500 mb-1">
          PDF · Image · Word · Excel · CSV
        </p>
        <p className="text-xs text-slate-400 dark:text-slate-500 mb-8">
          Select multiple files — they'll be processed one at a time
        </p>
        <div className="px-6 py-2 bg-slate-900 dark:bg-slate-700 text-white rounded-full font-medium hover:bg-slate-800 dark:hover:bg-slate-600 transition-colors">
          Select Files
        </div>
      </label>
    );
  }

  // ── Queue + processing view ──────────────────────────────────────────────
  return (
    <div className="space-y-4">

      {/* ── Batch summary (when all done) ── */}
      {allDone && !isRunning && (
        <div className={`rounded-2xl px-6 py-4 border flex items-center justify-between ${
          errorCount === 0
            ? 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800'
            : 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800'
        }`}>
          <div className="flex items-center gap-3">
            <CheckCircle2 size={22} className={errorCount === 0 ? 'text-green-600' : 'text-amber-500'} />
            <div>
              <p className="font-semibold text-slate-800 dark:text-slate-200 text-sm">
                Batch complete — {doneCount} of {queue.length} processed successfully
                {errorCount > 0 && `, ${errorCount} failed`}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Patient records saved. View them in the Patients section.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => navigate('/patients')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-colors"
            >
              View Patients
            </button>
            <button
              onClick={handleReset}
              className="p-2 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
              title="Process more files"
            >
              <RotateCcw size={18} />
            </button>
          </div>
        </div>
      )}

      {/* ── Active file progress ── */}
      {isRunning && activeItem && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="text-blue-500 animate-pulse">
              <currentStep.Icon size={22} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate">
                {activeItem.file.name}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">{currentStep.label}</p>
            </div>
            <span className="ml-auto text-xs font-mono text-blue-500">{progress}%</span>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-slate-100 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden mb-4">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-300 ease-linear"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Step list */}
          <div className="space-y-1">
            {PIPELINE_STEPS.map((step, i) => {
              const isActive    = i === stepIndex;
              const isCompleted = i < stepIndex;
              return (
                <div
                  key={i}
                  className={`flex items-center gap-2.5 px-2 py-1.5 rounded-lg text-xs transition-all ${
                    isActive    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                    : isCompleted ? 'text-slate-400 dark:text-slate-500'
                    : 'text-slate-300 dark:text-slate-600'
                  }`}
                >
                  <span className="w-4 text-center shrink-0">
                    {isCompleted
                      ? <CheckCircle2 size={12} className="text-blue-500 inline" />
                      : isActive
                      ? <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                      : <span className="inline-block w-1.5 h-1.5 rounded-full bg-slate-200 dark:bg-slate-700" />
                    }
                  </span>
                  <step.Icon size={11} className="shrink-0" />
                  {step.label}
                  {isActive && <span className="ml-auto text-blue-500 animate-pulse font-mono">running…</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── File queue list ── */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            {queue.length} file{queue.length !== 1 ? 's' : ''} queued
          </span>
          {isRunning && (
            <span className="text-xs text-slate-400">
              {doneCount + errorCount} / {queue.length} done
            </span>
          )}
        </div>

        <div className="divide-y divide-slate-100 dark:divide-slate-700/60 max-h-72 overflow-y-auto">
          {queue.map((item) => {
            const FileIcon = getFileIcon(item.file.name);
            const isActive = item.id === activeId;
            return (
              <div
                key={item.id}
                className={`flex items-center gap-3 px-5 py-3 transition-colors ${
                  isActive ? 'bg-blue-50 dark:bg-blue-900/10' : ''
                }`}
              >
                {/* File type icon */}
                <div className="shrink-0 text-slate-400 dark:text-slate-500">
                  <FileIcon size={18} />
                </div>

                {/* Name + size */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                    {item.file.name}
                  </p>
                  {item.status === 'error' ? (
                    <p className="text-xs text-red-500 truncate mt-0.5">{item.error}</p>
                  ) : (
                    <p className="text-xs text-slate-400">{formatSize(item.file.size)}</p>
                  )}
                </div>

                {/* Status indicator */}
                <div className="shrink-0">
                  {item.status === 'queued'     && <Clock    size={16} className="text-slate-300 dark:text-slate-600" />}
                  {item.status === 'processing' && <span className="inline-block w-4 h-4 border-2 border-blue-300 border-t-blue-600 rounded-full animate-spin" />}
                  {item.status === 'done'       && <CheckCircle2 size={16} className="text-green-500" />}
                  {item.status === 'error'      && <XCircle  size={16} className="text-red-500" />}
                </div>

                {/* Remove button (only when not running) */}
                {!isRunning && item.status === 'queued' && (
                  <button
                    onClick={() => removeFile(item.id)}
                    className="shrink-0 text-slate-300 dark:text-slate-600 hover:text-red-400 transition-colors"
                  >
                    <XCircle size={15} />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Actions row ── */}
      {!isRunning && !allDone && (
        <div className="flex items-center gap-3">
          {/* Add more files */}
          <label className="flex items-center gap-2 px-4 py-2.5 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 text-sm font-medium rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer">
            <input
              type="file"
              multiple
              className="hidden"
              onChange={handleInputChange}
              accept=".pdf,.jpg,.jpeg,.png,.webp,.tiff,.tif,.bmp,.docx,.xlsx,.xls,.csv"
            />
            <Plus size={15} /> Add More Files
          </label>

          {/* Drop area trigger */}
          <label
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 border-2 border-dashed rounded-xl text-sm text-slate-400 transition-colors cursor-pointer ${
              dragActive
                ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/10 text-blue-500'
                : 'border-slate-200 dark:border-slate-700 hover:border-blue-300'
            }`}
          >
            <input type="file" multiple className="hidden" onChange={handleInputChange}
              accept=".pdf,.jpg,.jpeg,.png,.webp,.tiff,.tif,.bmp,.docx,.xlsx,.xls,.csv" />
            <Upload size={14} /> Drop more files here
          </label>

          {/* Start button */}
          {queuedCount > 0 && (
            <button
              onClick={handleStart}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-colors shadow-sm"
            >
              <Play size={14} />
              Process {queuedCount} File{queuedCount !== 1 ? 's' : ''}
            </button>
          )}
        </div>
      )}

      {/* Retry failed + process more (after batch done) */}
      {!isRunning && allDone && errorCount > 0 && (
        <button
          onClick={() => {
            // Reset errored files back to queued, then run again
            setQueue(prev => prev.map(q => q.status === 'error' ? { ...q, status: 'queued', error: undefined } : q));
            setAllDone(false);
          }}
          className="flex items-center gap-2 px-4 py-2 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm font-medium rounded-xl hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors"
        >
          <RotateCcw size={14} /> Retry {errorCount} Failed File{errorCount !== 1 ? 's' : ''}
        </button>
      )}
    </div>
  );
};

export default FileUpload;
