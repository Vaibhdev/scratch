import { useState, useEffect } from 'react';
import { getRecords, bulkReview } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import ScopeBadge from '../components/ScopeBadge';
import RecordDetail from '../components/RecordDetail';

export default function Review() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecordId, setSelectedRecordId] = useState(null);
  const [selectedRowIds, setSelectedRowIds] = useState(new Set());
  
  // Filters
  const [filters, setFilters] = useState({
    review_status: 'PENDING',
    source_type: '',
    ghg_scope: '',
  });

  const fetchRecords = () => {
    setLoading(true);
    getRecords(filters).then(res => {
      setRecords(res.data.results || []);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchRecords();
  }, [filters]);

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setSelectedRowIds(new Set());
  };

  const toggleRow = (id, e) => {
    e.stopPropagation();
    const next = new Set(selectedRowIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedRowIds(next);
  };

  const toggleAll = () => {
    if (selectedRowIds.size === records.length) {
      setSelectedRowIds(new Set());
    } else {
      setSelectedRowIds(new Set(records.map(r => r.id)));
    }
  };

  const handleBulkAction = async (status) => {
    if (selectedRowIds.size === 0) return;
    await bulkReview({
      record_ids: Array.from(selectedRowIds),
      review_status: status,
    });
    setSelectedRowIds(new Set());
    fetchRecords();
  };

  return (
    <div>
      <div className="page-header">
        <h2>Review Board</h2>
        <p>Validate and approve ingested emissions data</p>
      </div>

      <div className="table-container">
        <div className="table-toolbar">
          <div className="filters">
            <select 
              value={filters.review_status} 
              onChange={e => handleFilterChange('review_status', e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="PENDING">Pending Review</option>
              <option value="APPROVED">Approved</option>
              <option value="FLAGGED">Flagged</option>
              <option value="REJECTED">Rejected</option>
            </select>
            
            <select 
              value={filters.source_type} 
              onChange={e => handleFilterChange('source_type', e.target.value)}
            >
              <option value="">All Source Types</option>
              <option value="SAP_PROCUREMENT">SAP Procurement</option>
              <option value="UTILITY_ELECTRICITY">Utility Electricity</option>
              <option value="TRAVEL_CONCUR">Concur Travel</option>
            </select>
            
            <select 
              value={filters.ghg_scope} 
              onChange={e => handleFilterChange('ghg_scope', e.target.value)}
            >
              <option value="">All Scopes</option>
              <option value="SCOPE_1">Scope 1</option>
              <option value="SCOPE_2">Scope 2</option>
              <option value="SCOPE_3">Scope 3</option>
            </select>
          </div>
          
          <div style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)' }}>
            Showing {records.length} records
          </div>
        </div>

        {selectedRowIds.size > 0 && (
          <div className="actions-bar">
            <span>{selectedRowIds.size} selected</span>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-sm btn-approve" onClick={() => handleBulkAction('APPROVED')}>Approve All</button>
              <button className="btn btn-sm btn-flag" onClick={() => handleBulkAction('FLAGGED')}>Flag All</button>
              <button className="btn btn-sm btn-reject" onClick={() => handleBulkAction('REJECTED')}>Reject All</button>
            </div>
          </div>
        )}

        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th style={{ width: '40px' }}>
                  <input 
                    type="checkbox" 
                    checked={records.length > 0 && selectedRowIds.size === records.length}
                    onChange={toggleAll}
                  />
                </th>
                <th>Status</th>
                <th>Scope</th>
                <th>Category</th>
                <th>Date</th>
                <th>Quantity</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '3rem' }}>Loading records...</td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '3rem' }}>No records found matching filters.</td>
                </tr>
              ) : (
                records.map(record => (
                  <tr key={record.id} onClick={() => setSelectedRecordId(record.id)}>
                    <td onClick={e => e.stopPropagation()}>
                      <input 
                        type="checkbox" 
                        checked={selectedRowIds.has(record.id)}
                        onChange={(e) => toggleRow(record.id, e)}
                      />
                    </td>
                    <td><StatusBadge status={record.review_status} /></td>
                    <td><ScopeBadge scope={record.ghg_scope} /></td>
                    <td>{record.category_display}</td>
                    <td>{record.activity_date}</td>
                    <td>{parseFloat(record.normalized_quantity).toString()} {record.normalized_unit}</td>
                    <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {record.description}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedRecordId && (
        <RecordDetail 
          recordId={selectedRecordId} 
          onClose={() => setSelectedRecordId(null)} 
          onUpdate={fetchRecords}
        />
      )}
    </div>
  );
}
