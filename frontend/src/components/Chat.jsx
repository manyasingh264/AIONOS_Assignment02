import React, { useState, useRef, useEffect } from 'react';

const TYPE_BADGE_STYLE = {
  NEW_ISSUE:              { bg: '#1B2A4A', color: '#E2E8F0' },
  FOLLOW_UP:              { bg: '#1E3A5F', color: '#BAE6FD' },
  CLARIFICATION_RESPONSE: { bg: '#78350F', color: '#FEF3C7' },
  ACKNOWLEDGEMENT:        { bg: '#14532D', color: '#D1FAE5' },
  CORRECTION:             { bg: '#431407', color: '#FED7AA' },
  HUMAN_HANDOFF_REQUEST:  { bg: '#7F1D1D', color: '#FEE2E2' },
  MULTI_INTENT:           { bg: '#312E81', color: '#E0E7FF' },
  OUT_OF_SCOPE:           { bg: '#374151', color: '#F3F4F6' },
  POLICY_INFO_QUESTION:   { bg: '#134E4A', color: '#CCFBF1' },
  TICKET_STATUS_QUERY:    { bg: '#0C4A6E', color: '#E0F2FE' },
  ALREADY_TRIED:          { bg: '#4C0519', color: '#FFE4E6' },
};

function TypeBadge({ type }) {
  if (!type) return null;
  const style = TYPE_BADGE_STYLE[type] || { bg: '#374151', color: '#F3F4F6' };
  return (
    <span style={{
      display: 'inline-block',
      marginTop: '5px',
      padding: '2px 8px',
      borderRadius: '2px',
      fontSize: '10px',
      fontWeight: '600',
      letterSpacing: '0.06em',
      textTransform: 'uppercase',
      fontFamily: 'DM Mono, monospace',
      backgroundColor: style.bg,
      color: style.color,
    }}>
      {type.replace(/_/g, ' ')}
    </span>
  );
}

const Chat = ({ messages, onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) { onSendMessage(input.trim()); setInput(''); }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) handleSubmit(e);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', minHeight: 0, padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {messages.length === 0 && (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <p style={{ fontSize: '13px', color: '#94A3B8', textAlign: 'center', lineHeight: '1.6' }}>
              Select an employee and describe the issue.<br />The agent will classify, retrieve policy, and respond.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{ maxWidth: '78%', display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              {/* Sender label */}
              <div style={{ fontSize: '10px', fontWeight: '600', letterSpacing: '0.06em', textTransform: 'uppercase', color: '#94A3B8', marginBottom: '3px', fontFamily: 'DM Mono, monospace' }}>
                {msg.role === 'user' ? 'Employee' : 'IT Agent'}
              </div>
              {/* Bubble */}
              <div style={{
                padding: '10px 14px',
                borderRadius: '2px',
                fontSize: '13.5px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
                ...(msg.role === 'user'
                  ? { backgroundColor: '#1B2A4A', color: '#F1F5F9', border: '1px solid #243656' }
                  : { backgroundColor: '#F8FAFC', color: '#1E293B', border: '1px solid #E2E8F0' }
                )
              }}>
                {msg.content}
              </div>
              {/* Classification badge */}
              {msg.role === 'assistant' && msg.messageType && (
                <TypeBadge type={msg.messageType} />
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isLoading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ maxWidth: '78%' }}>
              <div style={{ fontSize: '10px', fontWeight: '600', letterSpacing: '0.06em', textTransform: 'uppercase', color: '#94A3B8', marginBottom: '3px', fontFamily: 'DM Mono, monospace' }}>IT Agent</div>
              <div style={{ padding: '10px 16px', borderRadius: '2px', backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0', display: 'flex', gap: '5px', alignItems: 'center' }}>
                <span className="dot-1" style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#94A3B8', display: 'inline-block' }} />
                <span className="dot-2" style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#94A3B8', display: 'inline-block' }} />
                <span className="dot-3" style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#94A3B8', display: 'inline-block' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} style={{ padding: '12px 16px', borderTop: '1px solid #E2E8F0', backgroundColor: '#FAFAF9', display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your IT issue..."
          disabled={isLoading}
          style={{
            flex: 1,
            padding: '9px 12px',
            fontSize: '13.5px',
            border: '1px solid #CBD5E1',
            borderRadius: '2px',
            backgroundColor: '#FFFFFF',
            color: '#1B2A4A',
            fontFamily: 'inherit',
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          style={{
            padding: '9px 18px',
            fontSize: '13px',
            fontWeight: '600',
            backgroundColor: isLoading || !input.trim() ? '#CBD5E1' : '#1B2A4A',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '2px',
            cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
            fontFamily: 'inherit',
            letterSpacing: '0.02em',
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default Chat;
