import { useState } from 'react';
import { Play, Copy, Download } from 'lucide-react';
import { apiService } from '../services/api';
import { SparqlResponse } from '../types';

interface QueryPanelProps {
  onQueryResult?: (data: SparqlResponse) => void;
}

const PREDEFINED_QUERIES = [
  { id: 1, name: 'Actuatoare în LivingRoom', description: 'Actuators in the living room' },
  { id: 2, name: 'Actuatoare cu brand și preț', description: 'Actuators with brand and price' },
  { id: 3, name: 'Pași rutină și secvența lor', description: 'Routine steps and their sequence' },
  { id: 4, name: 'Acțiuni și actuatoare', description: 'Actions and their actuators' },
  { id: 5, name: 'Camere cu acțiuni', description: 'Rooms where actions take place' },
  { id: 6, name: 'Integrare completă', description: 'Full integration query' },
];

const DEFAULT_QUERY = `SELECT ?s ?p ?o WHERE {
  ?s ?p ?o
} LIMIT 100`;

export function QueryPanel({ onQueryResult }: QueryPanelProps) {
  const [query, setQuery] = useState(DEFAULT_QUERY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any[] | null>(null);

  const handleRunQuery = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.runSparqlQuery(query);
      setResults(response.results);
      if (onQueryResult) {
        onQueryResult(response);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  const handlePredefinedQuery = async (queryId: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.runPredefinedQuery(queryId);
      setResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyQuery = () => {
    navigator.clipboard.writeText(query);
  };

  const handleDownloadResults = () => {
    if (!results) return;
    const dataStr = JSON.stringify(results, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'sparql-results.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
        <h2 className="font-semibold text-slate-800">SPARQL Query</h2>
      </div>

      <div className="p-4 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">Query Editor</label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full h-24 px-3 py-2 border border-slate-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            placeholder="Enter SPARQL query..."
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleRunQuery}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
          >
            <Play className="w-4 h-4" />
            {loading ? 'Running...' : 'Run Query'}
          </button>
          <button
            onClick={handleCopyQuery}
            className="flex items-center gap-2 px-3 py-2 bg-slate-100 text-slate-700 rounded-md hover:bg-slate-200 transition-colors text-sm"
          >
            <Copy className="w-4 h-4" />
            Copy
          </button>
          {results && (
            <button
              onClick={handleDownloadResults}
              className="flex items-center gap-2 px-3 py-2 bg-slate-100 text-slate-700 rounded-md hover:bg-slate-200 transition-colors text-sm"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
          )}
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <div className="border-t border-slate-200 pt-4">
          <label className="block text-sm font-medium text-slate-700 mb-2">Predefined Queries</label>
          <div className="grid grid-cols-2 gap-2">
            {PREDEFINED_QUERIES.map((q) => (
              <button
                key={q.id}
                onClick={() => handlePredefinedQuery(q.id)}
                disabled={loading}
                className="text-left px-3 py-2 bg-slate-50 border border-slate-200 rounded-md hover:bg-slate-100 disabled:opacity-50 transition-colors text-sm"
              >
                <div className="font-medium text-slate-800">{q.name}</div>
                <div className="text-xs text-slate-500 mt-0.5">{q.description}</div>
              </button>
            ))}
          </div>
        </div>

        {results !== null && (
          <div className="border-t border-slate-200 pt-4">
            <label className="block text-sm font-medium text-slate-700 mb-2">Results</label>
            {results.length > 0 ? (
              <div className="overflow-x-auto max-h-80 overflow-y-auto border border-slate-200 rounded-md">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-slate-50">
                    <tr className="border-b border-slate-200">
                      {Object.keys(results[0]).map((key) => (
                        <th key={key} className="text-left py-2 px-3 font-semibold text-slate-700">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white">
                    {results.map((row, idx) => (
                      <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                        {Object.values(row).map((cell: any, cellIdx) => (
                          <td key={cellIdx} className="py-2 px-3 text-slate-600">
                            {typeof cell === 'object' ? cell.value || JSON.stringify(cell) : String(cell)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center text-slate-500 py-4 bg-slate-50 rounded-md">No results found</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
