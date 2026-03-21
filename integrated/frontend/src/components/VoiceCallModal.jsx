import React, { useState, useEffect } from 'react';

export default function VoiceCallModal({ client, onClose }) {
  const [status, setStatus] = useState('Calling...');
  const [timer, setTimer] = useState(0);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setStatus('Connected');
    }, 2000);

    let interval;
    if (status === 'Connected') {
      interval = setInterval(() => {
        setTimer(prev => prev + 1);
      }, 1000);
    }

    return () => {
      clearTimeout(timeout);
      clearInterval(interval);
    };
  }, [status]);

  const formatTime = (s) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="call-overlay">
      <div className="voice-call-card">
        <div className="call-avatar">{client.avatar}</div>
        <h3 className="call-name">{client.clientName}</h3>
        <p className="call-status">
          {status === 'Connected' ? formatTime(timer) : status}
        </p>
        <div className="call-actions">
          <button className="call-btn mute-btn">🎤</button>
          <button className="call-btn end-btn" onClick={onClose}>📞</button>
        </div>
      </div>
    </div>
  );
}
