'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, RefreshCw, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RowValidationError {
  row_number: number;
  report_id?: string;
  column_name?: string;
  error_type: string;
  message: string;
}

interface IngestionResult {
  ingestion_id: string;
  filename: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  duplicate_rows: number;
  imported_rows: number;
  errors: RowValidationError[];
  warnings: RowValidationError[];
  message: string;
}

interface FileUploadProps {
  onUploadSuccess?: (result: IngestionResult) => void;
  className?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess, className }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [resultData, setResultData] = useState<IngestionResult | null>(null);
  const [showLogs, setShowLogs] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<{ total_imported: number; total_analyzed: number; status: string } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Clean up interval on unmount
  React.useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const pollProgress = async (filename: string) => {
    try {
      const res = await fetch(`/api/v1/reports/ingestion-status/${encodeURIComponent(filename)}`);
      if (res.ok) {
        const data = await res.json();
        setAnalysisProgress(data);
        if (data.status === 'COMPLETED') {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        }
      }
    } catch (err) {
      console.error('Failed to fetch ingestion status', err);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadStatus('error');
      setResultData(null);
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
    setUploadStatus('idle');
    setResultData(null);
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setUploadStatus('idle');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch('/api/v1/reports/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Upload HTTP status: ${res.status}`);
      }

      const data: IngestionResult = await res.json();
      setResultData(data);
      setUploadStatus('success');

      if (data.imported_rows > 0) {
        setAnalysisProgress({ total_imported: data.imported_rows, total_analyzed: 0, status: 'PROCESSING' });
        pollIntervalRef.current = setInterval(() => pollProgress(data.filename), 2000);
      } else {
        setAnalysisProgress({ total_imported: 0, total_analyzed: 0, status: 'COMPLETED' });
      }

      if (onUploadSuccess) onUploadSuccess(data);
    } catch (err: any) {
      setUploadStatus('error');
      setResultData({
        ingestion_id: 'ERR',
        filename: selectedFile.name,
        total_rows: 0,
        valid_rows: 0,
        invalid_rows: 0,
        duplicate_rows: 0,
        imported_rows: 0,
        errors: [{ row_number: 0, error_type: 'ERROR', message: err.message || 'Upload failed' }],
        warnings: [],
        message: err.message || 'Failed to submit dataset to backend service.'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className={cn('w-full space-y-4', className)}>
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer transition-colors bg-industrial-900/60',
          dragActive
            ? 'border-blue-500 bg-blue-950/20'
            : 'border-industrial-700 hover:border-industrial-500'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          onChange={handleChange}
          className="hidden"
        />

        <Upload className="w-10 h-10 text-industrial-400 mb-3" />
        <h4 className="text-sm font-mono font-semibold text-industrial-100 uppercase tracking-wide">
          Drag & Drop Safety Dataset (CSV)
        </h4>
        <p className="text-xs text-industrial-400 font-sans mt-1">
          Or click to browse from local workstation. Max size: 50MB.
        </p>

        {selectedFile && (
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded bg-industrial-800 border border-industrial-600 text-xs font-mono text-industrial-200">
            <FileText className="w-4 h-4 text-blue-400" />
            <span>{selectedFile.name}</span>
            <span className="text-industrial-400 font-mono">
              ({(selectedFile.size / 1024).toFixed(1)} KB)
            </span>
          </div>
        )}
      </div>

      {selectedFile && uploadStatus !== 'success' && (
        <div className="flex justify-end">
          <button
            onClick={handleUploadSubmit}
            disabled={uploading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-semibold tracking-wider uppercase transition-colors disabled:opacity-50"
          >
            {uploading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Validating Dataset Schema...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Start Dataset Ingestion
              </>
            )}
          </button>
        </div>
      )}

      {/* Ingestion Results Breakdown */}
      {uploadStatus === 'success' && resultData && (
        <div className="p-5 rounded border border-industrial-700 bg-industrial-950 space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              <div>
                <h5 className="text-xs font-mono font-semibold text-industrial-100 uppercase tracking-wide">
                  {analysisProgress?.status === 'COMPLETED' ? 'Ingestion & Analysis Complete' : 'Analyzing Reports...'}
                </h5>
                <p className="text-xs text-industrial-400 font-mono mt-0.5">
                  {analysisProgress?.status === 'COMPLETED' 
                    ? `${resultData.filename} — ${resultData.message}`
                    : `Reports analyzed: ${analysisProgress?.total_analyzed || 0} / ${analysisProgress?.total_imported || 0}`
                  }
                </p>
              </div>
            </div>
            <a
              href="/reports"
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-semibold rounded uppercase tracking-wide"
            >
              View Reports
            </a>
          </div>

          <div className="grid grid-cols-4 gap-3 font-mono text-xs text-center">
            <div className="p-3 bg-industrial-900 rounded border border-industrial-800">
              <span className="text-industrial-400 block text-[10px]">TOTAL ROWS</span>
              <span className="text-industrial-100 text-sm font-semibold">{resultData.total_rows}</span>
            </div>
            <div className="p-3 bg-emerald-950/40 border border-emerald-800/60 rounded">
              <span className="text-emerald-400 block text-[10px]">IMPORTED</span>
              <span className="text-emerald-300 text-sm font-semibold">{resultData.imported_rows}</span>
            </div>
            <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded">
              <span className="text-amber-400 block text-[10px]">DUPLICATES (SKIPPED)</span>
              <span className="text-amber-300 text-sm font-semibold">{resultData.duplicate_rows}</span>
            </div>
            <div className="p-3 bg-red-950/40 border border-red-800/60 rounded">
              <span className="text-red-400 block text-[10px]">REJECTED</span>
              <span className="text-red-300 text-sm font-semibold">{resultData.invalid_rows}</span>
            </div>
          </div>

          {(resultData.errors.length > 0 || resultData.warnings.length > 0) && (
            <div className="space-y-2">
              <button
                onClick={() => setShowLogs(!showLogs)}
                className="inline-flex items-center gap-1.5 text-xs font-mono text-industrial-400 hover:text-industrial-200"
              >
                {showLogs ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                {showLogs ? 'Hide Ingestion Log Details' : `Show Log Details (${resultData.errors.length} errors, ${resultData.warnings.length} warnings)`}
              </button>

              {showLogs && (
                <div className="max-h-48 overflow-y-auto p-3 bg-industrial-900 rounded border border-industrial-800 space-y-1 text-xs font-mono">
                  {resultData.errors.map((err, idx) => (
                    <div key={`err-${idx}`} className="text-red-400 flex items-center gap-2">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>Row {err.row_number}: [ERROR] {err.message}</span>
                    </div>
                  ))}
                  {resultData.warnings.map((warn, idx) => (
                    <div key={`warn-${idx}`} className="text-amber-400 flex items-center gap-2">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                      <span>Row {warn.row_number}: [WARNING] {warn.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {uploadStatus === 'error' && resultData && (
        <div className="p-4 rounded border border-red-800/60 bg-red-950/20 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h5 className="text-xs font-mono font-semibold text-red-300 uppercase tracking-wide">
              Ingestion Error
            </h5>
            <p className="text-xs text-red-400 font-mono">{resultData.message}</p>
          </div>
        </div>
      )}
    </div>
  );
};
