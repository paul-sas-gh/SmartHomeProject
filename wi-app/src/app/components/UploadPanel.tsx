import { useState, useRef } from 'react';
import { Upload, FileText, Type } from 'lucide-react';
import { apiService } from '../services/api';
import { ProcessResponse } from '../types';

interface UploadPanelProps {
  onProcessComplete?: (data: ProcessResponse) => void;
}

export function UploadPanel({ onProcessComplete }: UploadPanelProps) {
  const [activeTab, setActiveTab] = useState<'file' | 'text'>('text');
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleTextSubmit = async () => {
    if (!text.trim()) {
      setError('Please enter some text');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await apiService.processText(text);
      setSuccess(`Processed successfully! ${response.entity_count} entities, ${response.relation_count} relations, ${response.triple_count} triples`);
      if (onProcessComplete) {
        onProcessComplete(response);
      }
      setText('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Processing failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await apiService.processFile(file);
      setSuccess(`File processed successfully! ${response.entity_count} entities, ${response.relation_count} relations, ${response.triple_count} triples`);
      if (onProcessComplete) {
        onProcessComplete(response);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'File processing failed');
    } finally {
      setLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
        <h2 className="font-semibold text-slate-800">NLP Processing</h2>
      </div>

      <div className="border-b border-slate-200">
        <div className="flex">
          <button
            onClick={() => setActiveTab('text')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === 'text'
                ? 'bg-white text-blue-600 border-b-2 border-blue-600'
                : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Type className="w-4 h-4" />
            Text Input
          </button>
          <button
            onClick={() => setActiveTab('file')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === 'file'
                ? 'bg-white text-blue-600 border-b-2 border-blue-600'
                : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
            }`}
          >
            <FileText className="w-4 h-4" />
            File Upload
          </button>
        </div>
      </div>

      <div className="p-4 space-y-3">
        {activeTab === 'text' ? (
          <>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Enter Smart Home Description
              </label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Example: The living room has smart lights and a thermostat. The bedroom has a motion sensor..."
                className="w-full h-24 px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              />
            </div>
            <button
              onClick={handleTextSubmit}
              disabled={loading || !text.trim()}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              <Upload className="w-4 h-4" />
              {loading ? 'Processing...' : 'Process Text'}
            </button>
          </>
        ) : (
          <>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Upload Text File (.txt)
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt"
                onChange={handleFileUpload}
                disabled={loading}
                className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 file:cursor-pointer disabled:opacity-50"
              />
            </div>
            <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-md border border-slate-200">
              Upload a .txt file containing your smart home description. The file will be processed through the NLP pipeline to extract entities and relationships.
            </div>
          </>
        )}

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {success && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-700">{success}</p>
          </div>
        )}
      </div>
    </div>
  );
}
