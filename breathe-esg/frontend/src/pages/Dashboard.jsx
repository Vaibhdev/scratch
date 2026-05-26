import { useEffect, useState } from 'react';
import { getRecordSummary, getClients } from '../api/client';
import ScopeBadge from '../components/ScopeBadge';

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getClients().then(res => {
      setClients(res.data);
      if (res.data.length > 0) setSelectedClient(res.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedClient) return;
    setLoading(true);
    getRecordSummary({ client_id: selectedClient }).then(res => {
      setSummary(res.data);
      setLoading(false);
    });
  }, [selectedClient]);

  return (
    <div>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Emissions data ingestion overview</p>
      </div>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <label style={{ color: 'var(--text-secondary)' }}>Select Client:</label>
          <select 
            value={selectedClient} 
            onChange={e => setSelectedClient(e.target.value)}
            style={{ width: '300px' }}
          >
            {clients.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div>Loading stats...</div>
      ) : summary ? (
        <>
          <div className="card-grid">
            <div className="card stat-card" style={{ '--stat-color': 'var(--accent)' }}>
              <div className="stat-value">{summary.total}</div>
              <div className="stat-label">Total Records Ingested</div>
            </div>
            
            <div className="card stat-card" style={{ '--stat-color': 'var(--scope1)' }}>
              <div className="stat-value">{summary.by_scope.SCOPE_1 || 0}</div>
              <div className="stat-label">Scope 1 Records</div>
            </div>
            
            <div className="card stat-card" style={{ '--stat-color': 'var(--scope2)' }}>
              <div className="stat-value">{summary.by_scope.SCOPE_2 || 0}</div>
              <div className="stat-label">Scope 2 Records</div>
            </div>
            
            <div className="card stat-card" style={{ '--stat-color': 'var(--scope3)' }}>
              <div className="stat-value">{summary.by_scope.SCOPE_3 || 0}</div>
              <div className="stat-label">Scope 3 Records</div>
            </div>
          </div>

          <div className="card-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <div className="card">
              <h3 style={{ marginBottom: '1.5rem', fontSize: '1.1rem' }}>By Review Status</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {Object.entries(summary.by_review_status).map(([status, count]) => (
                  <div key={status} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{status}</span>
                    <span style={{ fontWeight: 600 }}>{count}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="card">
              <h3 style={{ marginBottom: '1.5rem', fontSize: '1.1rem' }}>By Category</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {Object.entries(summary.by_category).map(([category, count]) => (
                  <div key={category} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{category}</span>
                    <span style={{ fontWeight: 600 }}>{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
