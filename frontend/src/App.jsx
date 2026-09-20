import React, { useState, useCallback } from 'react';
import Chat from './components/Chat';
import DecisionCard from './components/DecisionCard';
import SourceCard from './components/SourceCard';
import TicketCard from './components/TicketCard';
import ActivityLog from './components/ActivityLog';

const EMPLOYEES = [
  { id: 'REQ-01', name: 'Aditi Sharma' },
  { id: 'REQ-02', name: 'Vikram Chawla' },
  { id: 'REQ-03', name: 'Karan Mehta' },
  { id: 'REQ-04', name: 'Ritu Bhatia' },
  { id: 'REQ-05', name: 'Sanjay Oberoi' },
  { id: 'REQ-06', name: 'Meera Iyer' },
  { id: 'REQ-07', name: 'Farhan Ali' },
  { id: 'REQ-08', name: 'Ananya Reddy' },
  { id: 'REQ-09', name: 'Rohit Desai' },
  { id: 'REQ-10', name: 'Kavya Pillai' },
  { id: 'REQ-11', name: 'Nikhil Bansal' },
  { id: 'REQ-12', name: 'Sneha Kulkarni' },
  { id: 'REQ-13', name: 'Aman Gupta' },
  { id: 'REQ-14', name: 'Tanya Chopra' },
  { id: 'REQ-15', name: 'Rahul Menon' },
];

const SAMPLE_REQUESTS = [
  "Can I get Wi-Fi access for a guest visiting our office tomorrow?",
  "I think I got a phishing email asking for my login",
  "My VPN stopped working this morning, says credentials expired",
  "I'm locked out of my account, tried my password 6 times",
  "My laptop won't turn on at all, completely dead, had it about 3.5 years",
  "Requesting approval to install a browser extension for productivity tracking",
  "I've started working from home 4 days a week, how do I get a monitor?",
  "hey can you help, its not working",
  "My VPN stopped working and my mailbox is full",
  "How long do VPN credentials last?",
  "What is today's weather?",
  "Can I talk to a human?",
];

function makeSessionId(employeeId) {
  return employeeId ? `session_${employeeId}` : `session_guest`;
}

function App() {
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [sessionId, setSessionId] = useState(makeSessionId(''));
  const [messages, setMessages] = useState([]);
  const [lastResponse, setLastResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleEmployeeChange = useCallback(async (e) => {
    const newEmpId = e.target.value;
    const oldSessionId = sessionId;
    if (oldSessionId) {
      try { await fetch(`/api/sessions/${oldSessionId}`, { method: 'DELETE' }); } catch (_) { }
    }
    const newSessionId = makeSessionId(newEmpId);
    setSelectedEmployee(newEmpId);
    setSessionId(newSessionId);
    setMessages([]);
    setLastResponse(null);
  }, [sessionId]);

  const handleSendMessage = useCallback(async (message) => {
    setMessages((prev) => [...prev, { role: 'user', content: message }]);
    setIsLoading(true);
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, employee_id: selectedEmployee || null, session_id: sessionId }),
      });
      if (!response.ok) throw new Error('Failed');
      const data = await response.json();
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response, messageType: data.message_type }]);
      setLastResponse(data);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Request failed. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  }, [selectedEmployee, sessionId]);

  const handleClearChat = useCallback(async () => {
    if (sessionId) {
      try { await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' }); } catch (_) { }
    }
    setMessages([]);
    setLastResponse(null);
  }, [sessionId]);

  const selectedEmployeeName = EMPLOYEES.find(e => e.id === selectedEmployee)?.name || null;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#F7F6F3' }}>

      {/* Header */}
      <header className="app-header" style={{
        backgroundColor: '#1B2A4A',
        borderBottom: '1px solid #243656',
        padding: '0',
      }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '14px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Plain SVG shield — no lucide */}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#93C5FD" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            <div>
              <div className="app-header-title" style={{ fontSize: '15px', fontWeight: '600', color: '#F1F5F9', letterSpacing: '-0.01em' }}>
                Veridian IT Support
              </div>
              <div className="app-header-sub" style={{ fontSize: '11px', color: '#64748B', letterSpacing: '0.04em', textTransform: 'uppercase', fontWeight: '500' }}>
                Internal Service Agent
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {selectedEmployeeName && (
              <span className="session-badge" style={{
                fontSize: '12px',
                color: '#93C5FD',
                backgroundColor: '#243656',
                padding: '4px 10px',
                borderRadius: '2px',
                fontWeight: '500',
                border: '1px solid #2D4A7A',
              }}>
                {selectedEmployee} &middot; {selectedEmployeeName}
              </span>
            )}
            <button
              onClick={handleClearChat}
              style={{
                fontSize: '12px',
                color: '#94A3B8',
                backgroundColor: 'transparent',
                border: '1px solid #2D3F5E',
                padding: '5px 12px',
                borderRadius: '2px',
                cursor: 'pointer',
                fontFamily: 'inherit',
                fontWeight: '500',
              }}
            >
              Clear
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="app-main">

        {/* Left — Chat panel */}
        <div>
          <div className="chat-panel">
            {/* Employee selector row */}
            <div style={{ padding: '12px 16px', borderBottom: '1px solid #E2E8F0', backgroundColor: '#FAFAF9' }}>
              <label style={{ fontSize: '11px', fontWeight: '600', color: '#64748B', letterSpacing: '0.06em', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
                Employee
              </label>
              <select
                value={selectedEmployee}
                onChange={handleEmployeeChange}
                style={{
                  width: '100%',
                  padding: '7px 10px',
                  fontSize: '13px',
                  border: '1px solid #CBD5E1',
                  borderRadius: '2px',
                  backgroundColor: '#FFFFFF',
                  color: '#1B2A4A',
                  fontFamily: 'inherit',
                  outline: 'none',
                  cursor: 'pointer',
                }}
              >
                <option value="">Select employee...</option>
                {EMPLOYEES.map((emp) => (
                  <option key={emp.id} value={emp.id}>{emp.name} ({emp.id})</option>
                ))}
              </select>
            </div>

            {/* Chat area */}
            <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
              <Chat messages={messages} onSendMessage={handleSendMessage} isLoading={isLoading} />
            </div>
          </div>

          {/* Sample requests */}
          <div style={{ marginTop: '12px', backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '4px', padding: '14px 16px' }}>
            <div style={{ fontSize: '11px', fontWeight: '600', color: '#94A3B8', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px' }}>
              Test Scenarios
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {SAMPLE_REQUESTS.map((req, i) => (
                <button
                  key={i}
                  onClick={() => handleSendMessage(req)}
                  disabled={isLoading}
                  title={req}
                  style={{
                    fontSize: '12px',
                    padding: '5px 10px',
                    backgroundColor: '#F1F5F9',
                    border: '1px solid #E2E8F0',
                    borderRadius: '2px',
                    color: '#475569',
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    opacity: isLoading ? 0.5 : 1,
                    fontFamily: 'inherit',
                    fontWeight: '400',
                  }}
                >
                  {req.length > 42 ? req.substring(0, 42) + '...' : req}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right — Info panel */}
        <div className="info-panel">
          {lastResponse ? (
            <>
              <DecisionCard decision={lastResponse.decision} reason={lastResponse.recommended_action} messageType={lastResponse.message_type} />
              <SourceCard policySources={lastResponse.policy_sources} />
              {lastResponse.ticket && <TicketCard ticket={lastResponse.ticket} />}
              <ActivityLog audit={lastResponse.audit} />
            </>
          ) : (
            <div style={{
              backgroundColor: '#FFFFFF',
              border: '1px solid #E2E8F0',
              borderRadius: '4px',
              padding: '32px 20px',
              textAlign: 'center',
            }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" strokeWidth="1.5" style={{ margin: '0 auto 12px' }} strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <div style={{ fontSize: '13px', color: '#94A3B8', lineHeight: '1.5' }}>
                Send a message to see the agent decision, policy source, and audit trace.
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
