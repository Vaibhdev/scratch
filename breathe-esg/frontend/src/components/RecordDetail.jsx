import { useState, useEffect } from 'react';
import { getRecord, reviewRecord } from '../api/client';
import StatusBadge from './StatusBadge';
import ScopeBadge from './ScopeBadge';

export default function RecordDetail({ recordId, onClose, onUpdate }) {
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState('');
  const [actioning, setActioning] = useState(false);

  useEffect(() => {
    if (!recordId) return;
    setLoading(true);
    getRecord(recordId).then(res => {
      setRecord(res.data);
      setNotes(res.data.review_notes || '');
      setLoading(false);
    });
  }, [recordId]);

  const handleAction = async (status) => {
    setActioning(true);
    try {
      const res = await reviewRecord(recordId, { review_status: status, review_notes: notes });
      setRecord(res.data);
      if (onUpdate) onUpdate();
    } finally {
      setActioning(false);
    }
  };

  if (!recordId) return null;

  return (
    <>
      <div className="detail-panel-backdrop" onClick={onClose}></div>
      <div className="detail-panel">
        <div className="detail-header">
          <div>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>Record Details</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              From {record?.ingestion_file || 'unknown file'}
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="24" height="24">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        {loading ? (
          <div>Loading details...</div>
        ) : record ? (
          <>
            <div className="detail-section">
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                <StatusBadge status={record.review_status} />
                <ScopeBadge scope={record.ghg_scope} />
              </div>

              <h4>Core Information</h4>
              <div className="detail-field">
                <span className="label">Activity Date</span>
                <span className="value">{record.activity_date}</span>
              </div>
              <div className="detail-field">
                <span className="label">Category</span>
                <span className="value">{record.category_display}</span>
              </div>
              <div className="detail-field">
                <span className="label">Normalized Quantity</span>
                <span className="value">{record.normalized_quantity} {record.normalized_unit}</span>
              </div>
              <div className="detail-field">
                <span className="label">Original Quantity</span>
                <span className="value">{record.quantity} {record.original_unit}</span>
              </div>
              <div className="detail-field" style={{ borderBottom: 'none' }}>
                <span className="label">Description</span>
                <span className="value">{record.description}</span>
              </div>
            </div>

            <div className="detail-section">
              <h4>Review Actions</h4>
              <textarea 
                value={notes} 
                onChange={e => setNotes(e.target.value)}
                placeholder="Add review notes here..."
                style={{
                  width: '100%',
                  minHeight: '80px',
                  background: 'var(--bg-glass)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px',
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-family)',
                  fontSize: 'var(--font-sm)',
                  marginBottom: '1rem',
                  resize: 'vertical'
                }}
              />
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button 
                  className="btn btn-approve" 
                  onClick={() => handleAction('APPROVED')}
                  disabled={actioning || record.review_status === 'APPROVED'}
                >
                  Approve
                </button>
                <button 
                  className="btn btn-flag" 
                  onClick={() => handleAction('FLAGGED')}
                  disabled={actioning || record.review_status === 'FLAGGED'}
                >
                  Flag
                </button>
                <button 
                  className="btn btn-reject" 
                  onClick={() => handleAction('REJECTED')}
                  disabled={actioning || record.review_status === 'REJECTED'}
                >
                  Reject
                </button>
              </div>
            </div>

            <div className="detail-section">
              <h4>Source Metadata</h4>
              {Object.entries(record.source_metadata).map(([key, value]) => (
                value !== null && value !== '' && (
                  <div className="detail-field" key={key}>
                    <span className="label">{key}</span>
                    <span className="value">{value.toString()}</span>
                  </div>
                )
              ))}
            </div>

            <div className="detail-section">
              <h4>Raw Data</h4>
              <div className="raw-data-block">
                {JSON.stringify(record.raw_data, null, 2)}
              </div>
            </div>

            <div className="detail-section">
              <h4>Audit Trail</h4>
              {record.audit_entries?.map(entry => (
                <div className="audit-entry" key={entry.id}>
                  <div className={`audit-dot ${entry.action.toLowerCase()}`}></div>
                  <div>
                    <div style={{ fontSize: 'var(--font-sm)', fontWeight: 500 }}>
                      {entry.action_display}
                    </div>
                    <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>
                      by {entry.changed_by} on {new Date(entry.changed_at).toLocaleString()}
                    </div>
                    {entry.field_changed && (
                      <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        {entry.field_changed}: {entry.old_value} → {entry.new_value}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : null}
      </div>
    </>
  );
}
