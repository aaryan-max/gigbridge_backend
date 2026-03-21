import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { clientService } from "../services";

const DRAFT_KEY = "gb_client_profile_draft";

export default function ClientProfileSetup() {
  const navigate = useNavigate();
  const { markProfileCompleted } = useAuth();
  const [step, setStep] = useState(1);
  const [showToast, setShowToast] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [ripple, setRipple] = useState({ x: 0, y: 0, t: 0 });
  const [form, setForm] = useState({
    username: "",
    location: "",
    pin: "",
    phone: "",
    bio: "",
    dob: "",
  });

  useEffect(() => {
    const userData = JSON.parse(localStorage.getItem("gb_user_data") || "{}");
    const clientId = userData.id;
    if (clientId) {
      clientService.getProfile(clientId).then((data) => {
        if (data.success && (data.phone || data.location || data.bio)) {
          setForm((f) => ({
            ...f,
            username: data.name || f.username,
            location: data.location || f.location,
            pin: data.pincode || f.pin,
            phone: data.phone || f.phone,
            bio: data.bio || f.bio,
            dob: data.dob || f.dob,
          }));
          return;
        }
        loadDraft();
      }).catch(() => {
        loadDraft();
      });
    } else {
      loadDraft();
    }

    function loadDraft() {
      try {
        const raw = localStorage.getItem(DRAFT_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed.form) setForm((f) => ({ ...f, ...parsed.form }));
          if (parsed.step) setStep(parsed.step);
        }
      } catch {}
    }
  }, []);

  // Persist draft
  useEffect(() => {
    localStorage.setItem(DRAFT_KEY, JSON.stringify({ step, form }));
  }, [step, form]);

  const pct = useMemo(() => (step === 1 ? 50 : 100), [step]);

  const onField = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const continueToStep2 = (e) => {
    e.preventDefault();
    setStep(2);
  };

  const goBack = () => setStep(1);

  const playChime = () => {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.connect(g); g.connect(ctx.destination);
    o.type = "sine"; o.frequency.value = 880;
    g.gain.setValueAtTime(0.0001, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.05, ctx.currentTime + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.25);
    o.start(); o.stop(ctx.currentTime + 0.3);
  };

  const saveProfile = async (e) => {
    e.preventDefault();
    setSaveError("");
    const userData = JSON.parse(localStorage.getItem("gb_user_data") || "{}");
    const clientId = userData.id;
    if (!clientId) {
      setSaveError("Not logged in. Please log in again.");
      return;
    }
    try {
      const res = await clientService.createProfile({
        client_id: clientId,
        phone: form.phone,
        location: form.location,
        bio: form.bio || "",
        dob: form.dob || "",
        pincode: form.pin || "",
      });
      if (!res.success) {
        setSaveError(res.msg || "Failed to save profile. Please try again.");
        return;
      }
    } catch (err) {
      setSaveError(err.message || "Failed to save profile. Please try again.");
      return;
    }
    markProfileCompleted();
    setShowToast(true);
    playChime();
    setTimeout(() => {
      setShowToast(false);
      localStorage.removeItem(DRAFT_KEY);
      navigate("/onboarding", { replace: true });
    }, 1100);
  };

  const onPrimaryClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setRipple({ x: e.clientX - rect.left, y: e.clientY - rect.top, t: Date.now() });
  };

  return (
    <section className="cp-wrap cp-stage">
      <div className="cp-card cp-appear">
        <header className="cp-header">
          <span className="cp-pill">✨ Client Profile</span>
          <h3>Create Your Profile</h3>
          <p>{step === 1 ? "Step 1 of 2 — Basic Info" : "Step 2 of 2 — Contact & Bio"}</p>
        </header>

        <div className="cp-tabs">
          <span className={step === 1 ? "active" : ""}>Basic Info</span>
          <span className={step === 2 ? "active" : ""}>Contact & Bio</span>
        </div>

        <div className="cp-progress">
          <div className="cp-bar" style={{ width: `${pct}%` }} />
          <div className="cp-dot" style={{ left: `calc(${pct}% - 8px)` }} />
        </div>

        {step === 1 ? (
          <form className="cp-form cp-slide-in" onSubmit={continueToStep2}>
            <label>
              <span>Username</span>
              <div className="cp-input">
                <span className="cp-ico">👤</span>
                <input
                  type="text"
                  placeholder="johndoe"
                  value={form.username}
                  onChange={onField("username")}
                  required
                />
              </div>
            </label>

            <div className="cp-row">
              <label>
                <span>Location</span>
                <input
                  type="text"
                  placeholder="New York"
                  value={form.location}
                  onChange={onField("location")}
                  required
                />
              </label>
              <label>
                <span>Pin Code</span>
                <input
                  type="number"
                  placeholder="10001"
                  value={form.pin}
                  onChange={onField("pin")}
                  required
                />
              </label>
            </div>
            <button className="cp-primary" onClick={onPrimaryClick}>
              Continue <span className="cp-arrow">→</span>
              <span
                key={ripple.t}
                className="cp-ripple"
                style={{ left: ripple.x, top: ripple.y }}
              />
            </button>
          </form>
        ) : (
          <form className="cp-form cp-slide-in" onSubmit={saveProfile}>
            {saveError && <div style={{color: '#dc2626', marginBottom: '1rem', fontSize: '0.9rem', textAlign: 'center'}}>{saveError}</div>}
            <label>
              <span>Phone Number</span>
              <input
                type="tel"
                placeholder="+1 (555) 000-0000"
                value={form.phone}
                onChange={onField("phone")}
                required
              />
            </label>
            <label>
              <span>Bio</span>
              <textarea
                rows="4"
                placeholder="Tell us about yourself..."
                value={form.bio}
                onChange={onField("bio")}
              />
            </label>
            <label>
              <span>Date of Birth</span>
              <input
                type="date"
                value={form.dob}
                onChange={onField("dob")}
              />
            </label>
            <div className="cp-actions">
              <button type="button" className="cp-ghost" onClick={goBack}>← Back</button>
              <button className="cp-primary" onClick={onPrimaryClick}>
                <span className="cp-check" aria-hidden="true" /> Save Profile
                <span
                  key={ripple.t}
                  className="cp-ripple"
                  style={{ left: ripple.x, top: ripple.y }}
                />
              </button>
            </div>
          </form>
        )}
      </div>

      {showToast && (
        <div className="cp-toast">
          <span className="cp-toast-check">✔</span>
          Profile created successfully 🎉
        </div>
      )}
    </section>
  );
}
