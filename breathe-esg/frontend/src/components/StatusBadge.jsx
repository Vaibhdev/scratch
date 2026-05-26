export default function StatusBadge({ status }) {
  const map = {
    PENDING: { label: 'Pending', class: 'badge-pending' },
    APPROVED: { label: 'Approved', class: 'badge-approved' },
    FLAGGED: { label: 'Flagged', class: 'badge-flagged' },
    REJECTED: { label: 'Rejected', class: 'badge-rejected' },
    PROCESSING: { label: 'Processing', class: 'badge-pending' },
    COMPLETED: { label: 'Completed', class: 'badge-approved' },
    FAILED: { label: 'Failed', class: 'badge-rejected' },
  };

  const config = map[status] || { label: status, class: '' };

  return (
    <span className={`badge ${config.class}`}>
      {config.label}
    </span>
  );
}
