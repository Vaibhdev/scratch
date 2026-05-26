import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getClients, uploadFile } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function Upload() {
  const navigate = useNavigate();
  const [clients, setClients] = useState([]);
  const [clientId, setClientId] = useState('');
  const [sourceType, setSourceType] = useState('SAP_PROCUREMENT');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getClients().then(res => {
      setClients(res.data);
      if (res.data.length > 0) setClientId(res.data[0].id);
    });
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file || !clientId) return;
    
    setUploading(true);
    setError(null);
    setResult(null);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('client_id', clientId);
    formData.append('source_type', sourceType);

    try {
      const res = await uploadFile(formData);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed');
    } finally {
      setUploading(false);
      setFile(null); // Reset file input
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Upload Data</h2>
        <p>Ingest flat files and JSON exports from source systems</p>
      </div>

      <div className="card">
        <div className="upload-config">
          <div>
            <label>Client</label>
            <select value={clientId} onChange={e => setClientId(e.target.value)}>
              {clients.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label>Source System Format</label>
            <select value={sourceType} onChange={e => setSourceType(e.target.value)}>
              <option value="SAP_PROCUREMENT">SAP Procurement (CSV)</option>
              <option value="UTILITY_ELECTRICITY">Utility Portal (CSV)</option>
              <option value="TRAVEL_CONCUR">SAP Concur Travel (JSON)</option>
            </select>
          </div>
        </div>

        <div 
          className="upload-zone" 
          onDragOver={e => e.preventDefault()} 
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input').click()}
          style={{ marginTop: '2rem' }}
        >
          <input 
            type="file" 
            id="file-input" 
            style={{ display: 'none' }} 
            onChange={e => setFile(e.target.files[0])}
          />
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          {file ? (
            <h3>{file.name}</h3>
          ) : (
            <>
              <h3>Drag & drop your file here</h3>
              <p>or click to browse</p>
            </>
          )}
        </div>

        <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
          <button 
            className="btn btn-primary" 
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? 'Processing...' : 'Upload & Ingest'}
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ marginTop: '2rem', borderColor: 'var(--color-rejected)' }}>
          <h3 style={{ color: 'var(--color-rejected)' }}>Upload Failed</h3>
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="ingestion-result">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Ingestion Complete</h3>
            <StatusBadge status={result.status} />
          </div>
          
          <div className="ingestion-stats">
            <div className="ingestion-stat">
              <div className="number">{result.total_rows}</div>
              <div className="label">Total Rows</div>
            </div>
            <div className="ingestion-stat">
              <div className="number" style={{ color: 'var(--color-approved)' }}>
                {result.successful_rows}
              </div>
              <div className="label">Successful</div>
            </div>
            <div className="ingestion-stat">
              <div className="number" style={{ color: 'var(--color-rejected)' }}>
                {result.failed_rows}
              </div>
              <div className="label">Failed</div>
            </div>
          </div>
          
          <div style={{ marginTop: '2rem', textAlign: 'center' }}>
            <button className="btn btn-ghost" onClick={() => navigate('/review')}>
              View in Review Board
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
