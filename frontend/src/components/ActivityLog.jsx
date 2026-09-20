import React from 'react';

// Human-readable label + color dot for each event type
const EVENT_CONFIG = {
  REQUEST_RECEIVED:      { label: 'Request received',         dot: '#94A3B8' },
  MESSAGE_CLASSIFIED:    { label: 'Message classified',       dot: '#6366F1' },
  NEW_ISSUE_DETECTED:    { label: 'New issue detected',       dot: '#3B82F6' },
  FOLLOW_UP_DETECTED:    { label: 'Follow-up detected',       dot: '#8B5CF6' },
  INTENT_IDENTIFIED:     { label: 'Intent identified',        dot: '#0EA5E9' },
  POLICY_RETRIEVED:      { label: 'Policy retrieved',         dot: '#2563EB' },
  DECISION:              { label: 'Decision made',            dot: '#D97706' },
  TICKET_CREATED:        { label: 'Ticket created',           dot: '#16A34A' },
  TICKET_UPDATED:        { label: 'Ticket updated',           dot: '#16A34A' },
  CLARIFICATION_REQUESTED: { label: 'Clarification requested', dot: '#F59E0B' },
  CLARIFICATION_RESPONSE_RECEIVED: { label: 'Clarification answered', dot: '#10B981' },
  HUMAN_HANDOFF:         { label: 'Escalated to human',      dot: '#EF4444' },
  OUT_OF_SCOPE:          { label: 'Out of scope',            dot: '#9CA3AF' },
  MULTI_INTENT_DETECTED: { label: 'Multiple issues detected', dot: '#8B5CF6' },
  POLICY_INFO_QUESTION:  { label: 'Policy question',         dot: '#06B6D4' },
};

// Make detail text readable (remove underscores from values like "guest_wifi")
function humanize(str) {
  if (!str) return '';
  return str.replace(/_/g, ' ');
}

const ActivityLog = ({ audit }) => {
  if (!audit || audit.length === 0) return null;

  return (
    <div style={{
      backgroundColor: '#FFFFFF',
      border: '1px solid #E2E8F0',
      borderRadius: '4px',
      overflow: 'hidden',
    }}>
      {/* Card header */}
      <div style={{
        padding: '11px 16px',
        borderBottom: '1px solid #F1F5F9',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <span style={{ fontSize: '13px', fontWeight: '600', color: '#1E293B' }}>
          Audit Trace
        </span>
        <span style={{
          fontSize: '11px',
          color: '#94A3B8',
          fontFamily: 'DM Mono, monospace',
        }}>
          {audit.length} step{audit.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Steps */}
      <div style={{ padding: '8px 0' }}>
        {audit.map((event, i) => {
          const config = EVENT_CONFIG[event.event] || { label: humanize(event.event), dot: '#CBD5E1' };
          const isLast = i === audit.length - 1;

          return (
            <div key={i} style={{ display: 'flex', gap: '0', padding: '0 16px' }}>
              {/* Timeline column */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '20px', marginRight: '12px', flexShrink: 0 }}>
                {/* Dot */}
                <div style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: config.dot,
                  marginTop: '14px',
                  flexShrink: 0,
                  zIndex: 1,
                }} />
                {/* Connecting line */}
                {!isLast && (
                  <div style={{
                    width: 1,
                    flex: 1,
                    minHeight: '12px',
                    backgroundColor: '#E2E8F0',
                  }} />
                )}
              </div>

              {/* Content */}
              <div style={{ paddingTop: '10px', paddingBottom: isLast ? '10px' : '8px', flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '13px', fontWeight: '500', color: '#1E293B' }}>
                    {config.label}
                  </span>
                  <span style={{
                    fontSize: '11px',
                    fontFamily: 'DM Mono, monospace',
                    color: '#94A3B8',
                  }}>
                    {event.timestamp}
                  </span>
                </div>
                {event.details && (
                  <p style={{
                    margin: '2px 0 0',
                    fontSize: '12px',
                    color: '#64748B',
                    lineHeight: '1.5',
                    wordBreak: 'break-word',
                  }}>
                    {humanize(event.details.length > 60 ? event.details.substring(0, 60) + '...' : event.details)}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ActivityLog;
