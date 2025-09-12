'use client';

import { useState, useEffect } from 'react';
import { useDebugStore } from '@/lib/debug-store';
import { getApiCallHistory } from '@/lib/api';
import { apiClient } from '@/lib/api';

const DebugPanel = () => {
  const { visible, debugInfo, apiCalls, loading, error, setDebugInfo, setLoading, setError, clearApiCalls } = useDebugStore();
  const [refreshKey, setRefreshKey] = useState(0);

  // Fetch debug info from backend
  const fetchDebugInfo = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/v1/_debug');
      if (response.ok) {
        const data = await response.json();
        setDebugInfo(data);
      } else {
        setError(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Update API calls from history
  useEffect(() => {
    const updateApiCalls = () => {
      const history = getApiCallHistory();
      clearApiCalls();
      history.forEach(call => useDebugStore.getState().addApiCall(call));
    };

    updateApiCalls();
    const interval = setInterval(updateApiCalls, 1000);
    return () => clearInterval(interval);
  }, [clearApiCalls]);

  // Fetch debug info when panel opens
  useEffect(() => {
    if (visible && !debugInfo) {
      fetchDebugInfo();
    }
  }, [visible, debugInfo]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gray-800 text-white p-4 flex justify-between items-center">
          <h2 className="text-xl font-bold">Debug Panel</h2>
          <div className="flex gap-2">
            <button
              onClick={fetchDebugInfo}
              disabled={loading}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded text-sm"
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
            <button
              onClick={() => useDebugStore.getState().setVisible(false)}
              className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
            >
              Close
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[calc(90vh-80px)]">
          {/* Backend Debug Info */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">Backend Debug Info</h3>
            {error ? (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                Error: {error}
              </div>
            ) : debugInfo ? (
              <div className="bg-gray-100 p-4 rounded">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><strong>Debug Mode:</strong> {debugInfo.debug ? 'ON' : 'OFF'}</div>
                  <div><strong>Log Level:</strong> {debugInfo.log_level}</div>
                  <div><strong>Log Format:</strong> {debugInfo.log_format}</div>
                  <div><strong>Long Pause MS:</strong> {debugInfo.long_pause_ms}</div>
                  <div><strong>MongoDB DB:</strong> {debugInfo.mongo_db}</div>
                  <div><strong>Redis Status:</strong> 
                    <span className={debugInfo.redis_ok ? 'text-green-600' : 'text-red-600'}>
                      {debugInfo.redis_ok ? 'OK' : 'ERROR'}
                    </span>
                  </div>
                  <div><strong>Uptime:</strong> {debugInfo.uptime_s}s</div>
                </div>
              </div>
            ) : (
              <div className="text-gray-500">Loading debug info...</div>
            )}
          </div>

          {/* Frontend Environment */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">Frontend Environment</h3>
            <div className="bg-gray-100 p-4 rounded">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><strong>DEBUG Mode:</strong> {process.env.NEXT_PUBLIC_DEBUG === '1' ? 'ON' : 'OFF'}</div>
                <div><strong>API Base:</strong> {process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'}</div>
                <div><strong>Log API:</strong> {process.env.NEXT_PUBLIC_LOG_API === '1' ? 'ON' : 'OFF'}</div>
                <div><strong>Build Time:</strong> {new Date().toLocaleString()}</div>
              </div>
            </div>
          </div>

          {/* API Call History */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-semibold">API Call History</h3>
              <button
                onClick={clearApiCalls}
                className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm"
              >
                Clear
              </button>
            </div>
            {apiCalls.length > 0 ? (
              <div className="bg-gray-100 rounded overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-200">
                      <tr>
                        <th className="px-3 py-2 text-left">Method</th>
                        <th className="px-3 py-2 text-left">URL</th>
                        <th className="px-3 py-2 text-left">Status</th>
                        <th className="px-3 py-2 text-left">Duration</th>
                        <th className="px-3 py-2 text-left">Time</th>
                        <th className="px-3 py-2 text-left">Request ID</th>
                      </tr>
                    </thead>
                    <tbody>
                      {apiCalls.slice(-20).reverse().map((call, index) => (
                        <tr key={index} className="border-t">
                          <td className="px-3 py-2">
                            <span className={`px-2 py-1 rounded text-xs font-mono ${
                              call.method === 'GET' ? 'bg-green-100 text-green-800' :
                              call.method === 'POST' ? 'bg-blue-100 text-blue-800' :
                              call.method === 'PUT' ? 'bg-yellow-100 text-yellow-800' :
                              call.method === 'DELETE' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {call.method}
                            </span>
                          </td>
                          <td className="px-3 py-2 font-mono text-xs">{call.url}</td>
                          <td className="px-3 py-2">
                            <span className={`px-2 py-1 rounded text-xs ${
                              call.status && call.status >= 200 && call.status < 300 ? 'bg-green-100 text-green-800' :
                              call.status && call.status >= 400 ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {call.status || 'N/A'}
                            </span>
                          </td>
                          <td className="px-3 py-2 font-mono">
                            {call.duration_ms ? `${call.duration_ms.toFixed(1)}ms` : 'N/A'}
                          </td>
                          <td className="px-3 py-2 text-xs">
                            {new Date(call.timestamp).toLocaleTimeString()}
                          </td>
                          <td className="px-3 py-2 font-mono text-xs">
                            {call.request_id ? call.request_id.substring(0, 8) + '...' : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-gray-500 text-center py-4">No API calls yet</div>
            )}
          </div>

          {/* Keyboard Shortcuts */}
          <div className="text-sm text-gray-600">
            <strong>Keyboard Shortcuts:</strong> Ctrl+D to toggle debug panel
          </div>
        </div>
      </div>
    </div>
  );
};

export default DebugPanel;


