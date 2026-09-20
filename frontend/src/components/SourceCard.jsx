import React from 'react';

const SourceCard = ({ policySources }) => {
  if (!policySources || policySources.length === 0) return null;

  return (
    <div style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '4px', padding: '14px 16px' }}>
      <div style={{ fontSize: '10px', fontWeight: '600', color: '#94A3B8', letterSpacing: '0.06em', textTransform: 'uppercase', fontFamily: 'DM Mono, monospace', marginBottom: '10px' }}>
        Source Policy
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
        {policySources.map((source, i) => (
          <span key={i} style={{
            padding: '4px 10px',
            backgroundColor: '#1B2A4A',
            color: '#93C5FD',
            borderRadius: '2px',
            fontSize: '12px',
            fontWeight: '600',
            fontFamily: 'DM Mono, monospace',
            letterSpacing: '0.04em',
          }}>
            {source}
          </span>
        ))}
      </div>
    </div>
  );
};

export default SourceCard;
