import React from 'react';

const PRIORITY_STYLE = {
  High:   { color: '#DC2626', bg: '#FEF2F2', border: '#FECACA' },
  Medium: { color: '#D97706', bg: '#FFFBEB', border: '#FDE68A' },
  Low:    { color: '#16A34A', bg: '#F0FDF4', border: '#BBF7D0' },
};

const TicketCard = ({ ticket }) => {
  if (!ticket) return null;
  const pri = PRIORITY_STYLE[ticket.priority] || { color: '#6B7280', bg: '#F9FAFB', border: '#E5E7EB' };

  const rows = [
    { label: 'Ticket ID', value: ticket.ticket_id, mono: true },
    { label: 'Employee', value: ticket.employee },
    { label: 'Category', value: ticket.category },
    { label: 'Source', value: ticket.source, mono: true },
    ticket.destination ? { label: 'Routed to', value: ticket.destination } : null,
    { label: 'Status', value: ticket.status },
  ].filter(Boolean);

  return (
    <div style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '4px', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '10px 16px', borderBottom: '1px solid #E2E8F0', backgroundColor: '#1B2A4A', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '10px', fontWeight: '600', letterSpacing: '0.06em', textTransform: 'uppercase', color: '#93C5FD', fontFamily: 'DM Mono, monospace' }}>
          Ticket Created
        </span>
        <span style={{
          fontSize: '10px',
          fontWeight: '700',
          padding: '2px 8px',
          borderRadius: '2px',
          backgroundColor: pri.bg,
          color: pri.color,
          border: `1px solid ${pri.border}`,
          fontFamily: 'DM Mono, monospace',
          letterSpacing: '0.04em',
        }}>
          {ticket.priority}
        </span>
      </div>

      {/* Data rows */}
      <div style={{ padding: '0' }}>
        {rows.map((row, i) => (
          <div key={i} style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '8px 16px',
            borderBottom: i < rows.length - 1 ? '1px solid #F1F5F9' : 'none',
            fontSize: '12.5px',
          }}>
            <span style={{ color: '#94A3B8', fontWeight: '500', minWidth: '80px' }}>{row.label}</span>
            <span style={{
              color: '#1B2A4A',
              fontWeight: '500',
              fontFamily: row.mono ? 'DM Mono, monospace' : 'inherit',
              fontSize: row.mono ? '12px' : '12.5px',
              textAlign: 'right',
            }}>
              {row.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TicketCard;
