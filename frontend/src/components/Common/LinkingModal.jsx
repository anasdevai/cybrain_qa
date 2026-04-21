import React, { useState, useEffect } from 'react';
import { searchKnowledge, createLink } from '../../api/editorApi';
import { X, Search, Link as LinkIcon, Loader2 } from 'lucide-react';

const LinkingModal = ({ isOpen, onClose, sourceId, sourceType = 'sop', onLinkCreated }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [linking, setLinking] = useState(false);
  const [rationale, setRationale] = useState('');

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await searchKnowledge(query);
      // Filter out self and unsupported combinations if needed
      setResults(data.filter(r => r.id !== sourceId));
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };



  const handleLink = async (target) => {
    setLinking(true);
    try {
      // Logic to determine link_type based on source and target types
      let link_type = '';
      if (sourceType === 'sop' && target.type === 'deviation') link_type = 'sop-deviation';
      else if (sourceType === 'deviation' && target.type === 'capa') link_type = 'deviation-capa';
      else if (sourceType === 'capa' && target.type === 'audit') link_type = 'capa-audit';
      else if (sourceType === 'audit' && target.type === 'decision') link_type = 'audit-decision';
      else if (sourceType === 'decision' && target.type === 'sop') link_type = 'decision-sop';

      // Fallback for simple SOP linking
      if (!link_type && sourceType === 'sop') {
        if (target.type === 'capa') link_type = 'sop-deviation'; // Use deviation as proxy or add more types
        else if (target.type === 'audit') link_type = 'capa-audit'; // Proxy
        else link_type = 'sop-deviation'; // Default
      }

      await createLink({
        source_id: sourceId,
        target_id: target.id,
        link_type: link_type || 'sop-deviation', // Default
        rationale_text: rationale
      });

      if (onLinkCreated) onLinkCreated();
      onClose();
    } catch (err) {
      alert('Link creation failed');
    } finally {
      setLinking(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[80vh]">
        <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <LinkIcon size={20} className="text-secondary-600" />
            Entität verknüpfen
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition">
            <X size={24} />
          </button>
        </div>

        <div className="p-4 space-y-4 overflow-y-auto">
          <form onSubmit={handleSearch} className="relative">
            <input
              autoFocus
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Nach Entität suchen (Titel, Nummer...)"
              className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-secondary-500 focus:border-transparent transition"
            />
            <Search className="absolute left-3 top-3.5 text-gray-400" size={20} />
            <button
              type="submit"
              className="absolute right-2 top-2 bg-secondary-600 text-white px-3 py-1.5 rounded-md hover:bg-secondary-700 transition text-sm font-medium"
            >
              Suchen
            </button>
          </form>

          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-500 uppercase">Begründung (Optional)</label>
            <textarea
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              placeholder="Warum wird diese Entität verknüpft?"
              className="w-full p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm"
              rows={2}
            />
          </div>

          <div className="flex-1 space-y-2 min-h-[200px]">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                <Loader2 className="animate-spin mb-2" size={32} />
                <p>Suche...</p>
              </div>
            ) : results.length > 0 ? (
              results.map((result) => (
                <div
                  key={result.id}
                  className="flex items-center justify-between p-3 border border-gray-100 rounded-lg hover:border-secondary-500 hover:bg-secondary-50 transition group"
                >
                  <div className="flex items-center gap-3">
                    <span className={`w-8 h-8 rounded-full flex items-center justify-center text-lg ${result.sourceColorClass || 'bg-gray-100'}`}>
                      {result.sourceIcon || '📄'}
                    </span>
                    <div>
                      <div className="font-semibold text-gray-800 text-sm">{result.title}</div>
                      <div className="text-[10px] text-gray-500">{result.metadata} · {result.typeLabel}</div>
                    </div>
                  </div>
                  <button
                    disabled={linking}
                    onClick={() => handleLink(result)}
                    className="bg-gray-100 text-gray-600 px-4 py-1.5 rounded-md hover:bg-secondary-600 hover:text-white transition text-xs font-bold disabled:opacity-50"
                  >
                    {linking ? 'Verknüpfe...' : 'Verknüpfen'}
                  </button>
                </div>
              ))
            ) : query && !loading ? (
              <div className="text-center py-12 text-gray-400 italic">
                Keine Ergebnisse für "{query}"
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400 italic">
                Geben Sie einen Suchbegriff ein.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LinkingModal;
