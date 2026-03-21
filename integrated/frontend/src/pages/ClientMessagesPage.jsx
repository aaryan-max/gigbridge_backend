import React, { useState, useMemo } from 'react';
import Navbar from '../components/Navbar';
import ConversationList from '../components/ConversationList';
import ChatWindow from '../components/ChatWindow';
import VoiceCallModal from '../components/VoiceCallModal';
import VideoCallModal from '../components/VideoCallModal';
import { useAuth } from '../context/AuthContext';
import './dashboard.css';
import './messages.css';

const MOCK_ARTISTS_CONVERSATIONS = [
  { id: 'ca1', clientName: "John Smith (Dancer)", avatar: "JS", lastMessage: "I've updated the performance routine. Let me know!", time: "11:15 AM", unread: 1, online: true },
  { id: 'ca2', clientName: "Sarah (Photographer)", avatar: "SP", lastMessage: "The high-res photos are ready for download.", time: "Yesterday", unread: 0, online: true },
  { id: 'ca3', clientName: "DJ Alex", avatar: "DA", lastMessage: "I'll check the equipment list by tonight.", time: "2 days ago", unread: 0, online: false },
  { id: 'ca4', clientName: "Rahul (Musician)", avatar: "RM", lastMessage: "Can we confirm the setlist for the wedding?", time: "3 days ago", unread: 2, online: true },
];

const MOCK_MESSAGES = {
  'ca1': [
    { id: 'm1', sender: 'client', text: "Hi John, how is the routine coming along?", timestamp: "10:00 AM" },
    { id: 'm2', sender: 'freelancer', text: "It's coming along great! I've added a special solo part.", timestamp: "10:30 AM" },
    { id: 'm3', sender: 'client', text: "That sounds amazing. Can't wait to see it!", timestamp: "11:00 AM" },
    { id: 'm4', sender: 'freelancer', text: "I've updated the performance routine. Let me know!", timestamp: "11:15 AM" },
  ]
};

export default function ClientMessagesPage() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState(MOCK_ARTISTS_CONVERSATIONS);
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
    setConversations(prev => prev.map(c => c.id === id ? { ...c, unread: 0 } : c));
  };

  const handleSendMessage = (text) => {
    if (!selectedConvId) return;
    const newMessage = {
      id: Date.now().toString(),
      sender: 'client', // On this page, the user is the client
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => ({
      ...prev,
      [selectedConvId]: [...(prev[selectedConvId] || []), newMessage]
    }));
    setConversations(prev => prev.map(c => 
      c.id === selectedConvId ? { ...c, lastMessage: text, time: 'Just now' } : c
    ));
  };

  return (
    <div className="client-messages-layout">
      <div className="messages-page-wrapper">
        <main className={`messages-container ${isMobileListOpen ? 'list-view' : 'chat-view'}`}>
          <div className="messages-layout">
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
                  <p>Select an artist to start chatting.</p>
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
