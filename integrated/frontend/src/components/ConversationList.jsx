import React, { useState } from 'react';

export default function ConversationList({ conversations, selectedId, onSelect }) {
  const [search, setSearch] = useState('');

  const filtered = conversations.filter(c => 
    c.clientName.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="conv-list-container">
      <div className="search-wrap">
        <div className="search-input-inner">
          <span>🔍</span>
          <input 
            placeholder="Search clients or conversations" 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>
      <div className="conv-list-scroll">
        {filtered.map(conv => (
          <div 
            key={conv.id} 
            className={`conv-item ${selectedId === conv.id ? 'active' : ''}`}
            onClick={() => onSelect(conv.id)}
          >
            <div className="conv-avatar-wrap">
              <div className="conv-avatar">{conv.avatar}</div>
              {conv.online && <div className="online-status" />}
            </div>
            <div className="conv-info">
              <div className="conv-meta">
                <span className="conv-name">{conv.clientName}</span>
                <span className="conv-time">{conv.time}</span>
              </div>
              <div className="conv-last-msg">{conv.lastMessage}</div>
            </div>
            {conv.unread > 0 && <div className="conv-unread">{conv.unread}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
