import React from 'react';

const DECISION_STYLES = {
  RESOLVE:  { bg: '#F0FDF4', border: '#16A34A', label: '#15803D', dot: '#16A34A', text: 'Resolved' },
  CLARIFY:  { bg: '#FFFBEB', border: '#D97706', label: '#B45309', dot: '#D97706', text: 'Clarification Needed' },
  ESCALATE: { bg: '#FFF1F2', border: '#DC2626', label: '#B91C1C', dot: '#DC2626', text: 'Escalated' },
  ROUTE:    { bg: '#EFF6FF', border: '#2563EB', label: '#1D4ED8', dot: '#2563EB', text: 'Routed' },
};

const DecisionCard = ({ decision, reason, messageType }) => {
  if (!decision) return null;
  const s = DECISION_STYLES[decision] || { bg: '#F9FAFB', border: '#9CA3AF', label: '#6B7280', dot: '#9CA3AF', text: decision };

  return (
    <div style={{ backgroundColor: s.bg, border: `1px solid ${s.border}`, borderRadius: '4px', padding: '14px 16px' }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: s.dot, display: 'inline-block', flexShrink: 0 }} />
          <span style={{ fontSize: '13px', fontWeight: '700', color: s.label, letterSpacing: '-0.01em' }}>
            {s.text}
          </span>
        </div>
        {messageType && (
          <span style={{
            fontSize: '10px',
            fontWeight: '600',
            color: s.label,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            fontFamily: 'DM Mono, monospace',
            opacity: 0.75,
          }}>
            {messageType.replace(/_/g, ' ')}
          </span>
        )}
      </div>
      {/* Reason */}
      {reason && (
        <p style={{ fontSize: '12.5px', color: '#374151', lineHeight: '1.55', margin: 0, paddingLeft: '16px' }}>
          {reason}
        </p>
      )}
    </div>
  );
};

export default DecisionCard;
