export default function ScopeBadge({ scope }) {
  const map = {
    SCOPE_1: { label: 'Scope 1', class: 'badge-scope1' },
    SCOPE_2: { label: 'Scope 2', class: 'badge-scope2' },
    SCOPE_3: { label: 'Scope 3', class: 'badge-scope3' },
  };

  const config = map[scope] || { label: scope, class: '' };

  return (
    <span className={`badge ${config.class}`}>
      {config.label}
    </span>
  );
}
