import { useEffect, useState } from 'react';
import { getIngestions } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function IngestionHistory() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    getIngestions().then(res => setLogs(res.data));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h2>Ingestion History</h2>
        <p>Audit trail of all file uploads</p>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Client</th>
              <th>Source Type</th>
              <th>File Name</th>
              <th>Status</th>
              <th>Success / Total</th>
            </tr>
          </thead>
          <tbody>
            {logs.map(log => (
              <tr key={log.id}>
                <td>{new Date(log.uploaded_at).toLocaleString()}</td>
                <td>{log.client_name}</td>
                <td>{log.source_type_display}</td>
                <td>{log.file_name}</td>
                <td><StatusBadge status={log.status} /></td>
                <td>
                  <span style={{ color: 'var(--color-approved)', fontWeight: 500 }}>
                    {log.successful_rows}
                  </span>
                  {' / '}
                  {log.total_rows}
                </td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '3rem' }}>
                  No ingestion logs found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
