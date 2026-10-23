import React, { useState } from 'react';
import { Upload, X, AlertCircle, FileArchive, CheckCircle2, ShieldCheck } from 'lucide-react';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadZip: (file: File) => Promise<void>;
  onUseSample: () => Promise<void>;
  isLoading: boolean;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUploadZip,
  onUseSample,
  isLoading,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError('Please upload a .ZIP archive.');
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError('Please upload a .ZIP archive.');
      }
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;
    try {
      await onUploadZip(selectedFile);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    }
  };

  const handleSampleSubmit = async () => {
    try {
      await onUseSample();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Sample load failed');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-3xl bg-white border border-slate-200/90 shadow-2xl p-7 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
              <FileArchive className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Upload .NET Repository</h3>
              <p className="text-xs text-slate-500">Analyze legacy codebase into an evidence-backed BRD</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
            <span className="font-medium">{error}</span>
          </div>
        )}

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
            dragOver ? 'border-indigo-500 bg-indigo-50/50' : 'border-slate-300 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-400'
          }`}
          onClick={() => document.getElementById('repo-file-input')?.click()}
        >
          <input
            id="repo-file-input"
            type="file"
            accept=".zip"
            className="hidden"
            onChange={handleFileChange}
          />
          <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Upload className="w-6 h-6" />
          </div>
          <p className="text-sm font-semibold text-slate-800">
            {selectedFile ? selectedFile.name : 'Click to select or drag and drop your .NET codebase (.zip)'}
          </p>
          <p className="text-xs text-slate-500 mt-1">Maximum size: 100MB. Clean zip archive.</p>
        </div>

        {/* Security Safeguards Callout */}
        <div className="rounded-xl bg-slate-50 border border-slate-200/80 p-3.5 space-y-1">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-indigo-700">
            <ShieldCheck className="w-4 h-4 text-indigo-600" />
            <span>Active Security Safeguards</span>
          </div>
          <p className="text-[11px] text-slate-600 leading-normal">
            Path traversal defense, symlink rejection, decompression bomb limits, binary file exclusion,
            and isolated temporary directory extraction.
          </p>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
          <button
            type="button"
            onClick={handleSampleSubmit}
            disabled={isLoading}
            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium underline underline-offset-4"
          >
            Or use LegacyOrders sample
          </button>

          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!selectedFile || isLoading}
              className="px-5 py-2.5 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 transition-all shadow-sm"
            >
              {isLoading ? 'Uploading...' : 'Start Ingestion'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
