import React, { useState, useEffect, useRef } from 'react';

export default function VideoCallModal({ client, onClose }) {
  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);
  const localVideoRef = useRef(null);

  useEffect(() => {
    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Error accessing camera:", err);
      }
    }
    if (camOn) {
      startCamera();
    } else {
      if (localVideoRef.current && localVideoRef.current.srcObject) {
        const tracks = localVideoRef.current.srcObject.getTracks();
        tracks.forEach(track => track.stop());
        localVideoRef.current.srcObject = null;
      }
    }
    return () => {
      if (localVideoRef.current && localVideoRef.current.srcObject) {
        const tracks = localVideoRef.current.srcObject.getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, [camOn]);

  return (
    <div className="call-overlay">
      <div className="video-call-window">
        <div className="remote-video">
          <div className="call-avatar" style={{ width: 120, height: 120, fontSize: 40 }}>{client.avatar}</div>
          <p style={{ marginTop: 20 }}>{client.clientName}</p>
          <p style={{ fontSize: 14, opacity: 0.7 }}>Client Video Unavailable (Simulation)</p>
        </div>
        
        <div className="local-video-preview">
          {camOn ? (
            <video ref={localVideoRef} autoPlay playsInline muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <div style={{ width: '100%', height: '100%', display: 'grid', placeItems: 'center', color: '#fff' }}>
              Camera Off
            </div>
          )}
        </div>

        <div className="video-controls">
          <button className={`call-btn ${!micOn ? 'end-btn' : 'mute-btn'}`} onClick={() => setMicOn(!micOn)}>
            {micOn ? '🎤' : '🔇'}
          </button>
          <button className={`call-btn ${!camOn ? 'end-btn' : 'mute-btn'}`} onClick={() => setCamOn(!camOn)}>
            {camOn ? '📹' : '📵'}
          </button>
          <button className="call-btn end-btn" onClick={onClose}>📞</button>
        </div>
      </div>
    </div>
  );
}
