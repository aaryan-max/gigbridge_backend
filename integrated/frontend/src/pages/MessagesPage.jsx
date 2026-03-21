import React, { useState, useEffect, useMemo } from 'react';
import DashboardHeader from '../components/DashboardHeader';
import DashboardSidebar from '../components/DashboardSidebar';
import ConversationList from '../components/ConversationList';
import ChatWindow from '../components/ChatWindow';
import VoiceCallModal from '../components/VoiceCallModal';
import VideoCallModal from '../components/VideoCallModal';
import { useAuth } from '../context/AuthContext';
import './dashboard.css';
import './messages.css';

const MOCK_CONVERSATIONS = [
  { id: 'c1', clientName: "Wedding Planner Co.", avatar: "WP", lastMessage: "Thanks for the update! The choreography looks great.", time: "10:30 AM", unread: 2, online: true },
  { id: 'c2', clientName: "Event Manager Rahul", avatar: "ER", lastMessage: "Can we schedule a call tomorrow to discuss the music list?", time: "Yesterday", unread: 0, online: false },
  { id: 'c3', clientName: "Music Festival Team", avatar: "MF", lastMessage: "The contract has been approved. Welcome aboard!", time: "2 days ago", unread: 1, online: true },
  { id: 'c4', clientName: "Fashion Studio", avatar: "FS", lastMessage: "When can you start the shoot?", time: "3 days ago", unread: 0, online: false },
  { id: 'c5', clientName: "Dance Academy", avatar: "DA", lastMessage: "We need a lead instructor for the workshop.", time: "4 days ago", unread: 0, online: true },
];

const MOCK_MESSAGES = {
  'c1': [
    { id: 'm1', sender: 'client', text: "Hi! I reviewed the initial routine you sent.", timestamp: "10:15 AM" },
    { id: 'm2', sender: 'freelancer', text: "Great! What do you think? Any changes needed?", timestamp: "10:16 AM" },
    { id: 'm3', sender: 'client', text: "They look fantastic! I especially love the transition in the second half.", timestamp: "10:18 AM" },
    { id: 'm4', sender: 'freelancer', text: "I'm glad you like them! I focused on making the movements clean and impactful.", timestamp: "10:20 AM" },
    { id: 'm5', sender: 'client', text: "Perfect! Can you proceed with the next segment?", timestamp: "10:22 AM" },
  ],
  'c2': [
    { id: 'm6', sender: 'client', text: "Hi, are you available for a corporate event next month?", timestamp: "Yesterday" },
  ]
};

export default function MessagesPage() {
  const { user } = useAuth();
  const [activeSidebar, setActiveSidebar] = useState('messages');
  const [conversations, setConversations] = useState(MOCK_CONVERSATIONS);
  const [selectedConvId, setSelectedId] = useState(null);
  const [messages, setMessages] = useState(MOCK_MESSAGES);
  const [isVoiceModalOpen, setVoiceOpen] = useState(false);
  const [isVideoModalOpen, setVideoOpen] = useState(false);
  const [isMobileListOpen, setMobileListOpen] = useState(true);

  const selectedConv = useMemo(() => 
    conversations.find(c => c.id === selectedConvId), 
    [selectedConvId, conversations]
  );

  const handleSelectConv = (id) => {
    setSelectedId(id);
    setMobileListOpen(false);
    // Mark as read
    setConversations(prev => prev.map(c => c.id === id ? { ...c, unread: 0 } : c));
  };

  const handleSendMessage = (text) => {
    if (!selectedConvId) return;
    const newMessage = {
      id: Date.now().toString(),
      sender: 'freelancer',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => ({
      ...prev,
      [selectedConvId]: [...(prev[selectedConvId] || []), newMessage]
    }));
    // Update last message in conversation list
    setConversations(prev => prev.map(c => 
      c.id === selectedConvId ? { ...c, lastMessage: text, time: 'Just now' } : c
    ));
  };

  return (
    <div className="db-layout">
      <DashboardHeader />
      <div className="db-shell chat-shell">
        <DashboardSidebar active={activeSidebar} onSelect={setActiveSidebar} />
        <main className={`db-main messages-container ${isMobileListOpen ? 'list-view' : 'chat-view'}`}>
          <div className="messages-layout">
            {/* Conversations List */}
            <div className={`conv-list-panel ${!isMobileListOpen ? 'mobile-hide' : ''}`}>
              <div className="panel-header">
                <h3>Messages</h3>
              </div>
              <ConversationList 
                conversations={conversations} 
                selectedId={selectedConvId}
                onSelect={handleSelectConv}
              />
            </div>

            {/* Chat Area */}
            <div className={`chat-panel ${isMobileListOpen ? 'mobile-hide' : ''}`}>
              {selectedConv ? (
                <ChatWindow 
                  conversation={selectedConv}
                  messages={messages[selectedConvId] || []}
                  onSend={handleSendMessage}
                  onVoiceCall={() => setVoiceOpen(true)}
                  onVideoCall={() => setVideoOpen(true)}
                  onBack={() => setMobileListOpen(true)}
                />
              ) : (
                <div className="chat-empty-state">
                  <div className="empty-icon">💬</div>
                  <p>Select a conversation to start chatting with clients.</p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {isVoiceModalOpen && selectedConv && (
        <VoiceCallModal 
          client={selectedConv} 
          onClose={() => setVoiceOpen(false)} 
        />
      )}

      {isVideoModalOpen && selectedConv && (
        <VideoCallModal 
          client={selectedConv} 
          onClose={() => setVideoOpen(false)} 
        />
      )}
    </div>
  );
}
