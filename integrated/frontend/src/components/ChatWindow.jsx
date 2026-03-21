import React, { useState, useRef, useEffect } from 'react';

export default function ChatWindow({ conversation, messages, onSend, onVoiceCall, onVideoCall, onBack }) {
  const [text, setText] = useState('');
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSend(text);
    setText('');
  };

  return (
    <>
      <header className="chat-header">
        <div className="chat-client-info">
          <button className="back-btn mobile-only" onClick={onBack}>←</button>
          <div className="conv-avatar">{conversation.avatar}</div>
          <div className="chat-client-text">
            <h4>{conversation.clientName}</h4>
            <span className={`chat-client-status ${conversation.online ? 'online' : ''}`}>
              {conversation.online ? '● Active now' : 'Offline'}
            </span>
          </div>
        </div>
        <div className="chat-actions">
          <button className="chat-act-btn" onClick={onVoiceCall} title="Voice Call">📞</button>
          <button className="chat-act-btn" onClick={onVideoCall} title="Video Call">📹</button>
          <button className="chat-act-btn" title="More">⋮</button>
        </div>
      </header>

      <div className="chat-messages" ref={scrollRef}>
        {messages.map(msg => (
          <div key={msg.id} className={`msg-bubble-wrap ${msg.sender}`}>
            <div className="msg-bubble">
              {msg.text}
            </div>
            <span className="msg-time">{msg.timestamp}</span>
          </div>
        ))}
      </div>

      <form className="chat-input-area" onSubmit={handleSend}>
        <div className="input-actions">
          <button type="button" className="input-act-btn">📎</button>
          <button type="button" className="input-act-btn">😊</button>
        </div>
        <div className="input-field-wrap">
          <input 
            placeholder="Type a message..." 
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </div>
        <button type="submit" className="send-btn">
          <span>➤</span>
        </button>
      </form>
    </>
  );
}
