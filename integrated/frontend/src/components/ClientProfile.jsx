import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { clientService } from "../services";
import { CalendarDays, MapPin, Star, Phone, Mail, User, CreditCard as Edit2, LogOut, ShieldCheck } from "lucide-react";

const RV = [
  { id: "alex", name: "Alex Rivera", role: "Musician", avatar: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=256&auto=format&fit=crop" },
  { id: "priya", name: "Priya Sharma", role: "Designer", avatar: "https://images.unsplash.com/photo-1547425260-76bcadfb4f2c?q=80&w=256&auto=format&fit=crop" },
  { id: "james", name: "James Cole", role: "Film Director", avatar: "https://images.unsplash.com/photo-1544717305-996b815c338c?q=80&w=256&auto=format&fit=crop" },
  { id: "mei", name: "Mei Lin", role: "Illustrator", avatar: "https://images.unsplash.com/photo-1527980965255-d3b416303d12?q=80&w=256&auto=format&fit=crop" }
];

export default function ClientProfile() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const fileRef = useRef(null);

  const [draft, setDraft] = useState({
    name: "",
    email: "",
    phone: "",
    location: "",
    bio: "",
    dob: "",
    avatar: "",
  });
  const [original, setOriginal] = useState(draft);
  const [saving, setSaving] = useState(false);
  const [savedToast, setSavedToast] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const userData = JSON.parse(localStorage.getItem("gb_user_data") || "{}");
    const clientId = userData.id;
    if (!clientId) {
      setLoading(false);
      return;
    }
    clientService.getProfile(clientId).then((data) => {
      if (data.success) {
        const profile = {
          name: data.name || userData.name || "",
          email: data.email || userData.email || "",
          phone: data.phone || "",
          location: data.location || "",
          bio: data.bio || "",
          dob: data.dob || "",
          avatar: data.profile_image || localStorage.getItem("client_profile_avatar") || "",
        };
        setDraft(profile);
        setOriginal(profile);
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const onField = (k) => (e) => setDraft((d) => ({ ...d, [k]: e.target.value }));

  const onPickAvatar = () => fileRef.current?.click();
  const onFile = (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      setDraft((d) => ({ ...d, avatar: reader.result }));
    };
    reader.readAsDataURL(f);
  };

  const save = async () => {
    setSaving(true);
    const userData = JSON.parse(localStorage.getItem("gb_user_data") || "{}");
    const clientId = userData.id;
    if (clientId) {
      try {
        await clientService.createProfile({
          client_id: clientId,
          phone: draft.phone,
          location: draft.location,
          bio: draft.bio || "",
          dob: draft.dob || "",
          pincode: "",
        });
      } catch {}
    }
    if (draft.avatar) localStorage.setItem("client_profile_avatar", draft.avatar);
    setOriginal(draft);
    setSaving(false);
    setSavedToast(true);
    setTimeout(() => setSavedToast(false), 1100);
  };
  const cancel = () => setDraft(original);

  const rating = 4.8;
  const [stats, setStats] = useState({ posted: 0, active: 0, messages: 0 });

  const computeStats = () => {
    try {
      const pRaw = localStorage.getItem("gb_projects");
      const projs = pRaw ? JSON.parse(pRaw) : [];
      const posted = projs.length;
      const active = projs.filter((p) => p.status === "active").length;
      const mRaw = localStorage.getItem("gb_messages");
      const msgs = mRaw ? JSON.parse(mRaw) : [];
      setStats({ posted, active, messages: msgs.length });
    } catch {
      setStats({ posted: 0, active: 0, messages: 0 });
    }
  };
  useEffect(() => {
    computeStats();
    const onStorage = () => computeStats();
    const onMsg = () => computeStats();
    const onProj = () => computeStats();
    window.addEventListener("storage", onStorage);
    window.addEventListener("gb:messages", onMsg);
    window.addEventListener("gb:projects", onProj);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("gb:messages", onMsg);
      window.removeEventListener("gb:projects", onProj);
    };
  }, []);
  const since = localStorage.getItem("client_profile_member_since") || (() => {
    const m = new Date();
    const v = m.toLocaleString("en-US", { month: "short", year: "numeric" });
    localStorage.setItem("client_profile_member_since", v);
    return v;
  })();

  if (loading) {
    return (
      <main className="clientp-wrap">
        <section className="clientp-hero">
          <div className="clientp-hero-inner">
            <h1 className="clientp-title">Loading profile...</h1>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="clientp-wrap">
      <section className="clientp-hero">
        <div className="clientp-hero-inner">
          <div className="clientp-eyebrow">MY ACCOUNT</div>
          <h1 className="clientp-title">Client Profile</h1>
          <p className="clientp-sub">Manage your profile, activity, and account settings</p>
        </div>
      </section>

      <section className="clientp-grid">
        <aside className="clientp-left fade-in">
          <div className="clientp-card">
            <div className="clientp-avatar-wrap">
              <img
                src={draft.avatar || "/assets/hero-image.png"}
                alt={draft.name}
                className="clientp-avatar"
              />
              <button className="clientp-avatar-edit" onClick={onPickAvatar} aria-label="Edit photo">
                <Edit2 size={16} />
              </button>
              <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }} onChange={onFile} />
            </div>
            <div className="clientp-name">{draft.name}</div>
            <p className="clientp-bio">{draft.bio || "Tell artists about yourself."}</p>
            <div className="clientp-rating">
              <Star size={16} color="#f59e0b" fill="#f59e0b" />
              <Star size={16} color="#f59e0b" fill="#f59e0b" />
              <Star size={16} color="#f59e0b" fill="#f59e0b" />
              <Star size={16} color="#f59e0b" fill="#f59e0b" />
              <Star size={16} color="#f59e0b" />
              <span>{rating}</span>
            </div>
            <div className="clientp-meta">
              <div className="clientp-meta-row">
                <MapPin size={16} />
                <span>{draft.location || "—"}</span>
              </div>
              <div className="clientp-meta-row">
                <CalendarDays size={16} />
                <span>Member since {since}</span>
              </div>
            </div>
            <div className="clientp-tags">
              <span className="clientp-tag"><ShieldCheck size={14} /> Verified Client</span>
              <span className="clientp-tag">Top Hirer</span>
            </div>
            <button className="clientp-primary" onClick={() => {}}>
              Edit Profile
            </button>
          </div>
        </aside>

        <section className="clientp-right fade-in">
          <div className="clientp-form">
            <div className="clientp-form-title">Profile Details</div>
            <div className="clientp-form-grid">
              <label className="clientp-field">
                <span className="clientp-label"><User size={14} /> Full Name</span>
                <input value={draft.name} onChange={onField("name")} placeholder="Full Name" />
              </label>
              <label className="clientp-field">
                <span className="clientp-label"><Mail size={14} /> Email Address</span>
                <input value={draft.email} onChange={onField("email")} placeholder="Email" type="email" />
              </label>
              <label className="clientp-field">
                <span className="clientp-label"><Phone size={14} /> Phone Number</span>
                <input value={draft.phone} onChange={onField("phone")} placeholder="+1 (555) 000-0000" />
              </label>
              <label className="clientp-field">
                <span className="clientp-label"><CalendarDays size={14} /> Date of Birth</span>
                <input value={draft.dob} onChange={onField("dob")} type="date" />
              </label>
              <label className="clientp-field full">
                <span className="clientp-label"><MapPin size={14} /> Location</span>
                <input value={draft.location} onChange={onField("location")} placeholder="City, Country" />
              </label>
              <label className="clientp-field full">
                <span className="clientp-label">Bio</span>
                <textarea rows="4" value={draft.bio} onChange={onField("bio")} placeholder="Write a short bio" />
              </label>
            </div>
            <div className="clientp-actions">
              <button className="clientp-primary" onClick={save} disabled={saving}>
                Save Changes
              </button>
              <button className="clientp-ghost" onClick={cancel}>Cancel</button>
            </div>
          </div>

          <div className="clientp-panel">
            <div className="clientp-panel-title">Recently Viewed Artists</div>
            <div className="clientp-recent">
              {RV.map((a) => (
                <div key={a.id} className="clientp-artist">
                  <img src={a.avatar} alt={a.name} />
                  <div className="clientp-artist-name">{a.name}</div>
                  <div className="clientp-artist-role">{a.role}</div>
                  <button className="clientp-link" onClick={() => navigate(`/artist/${a.id}`)}>View Profile</button>
                </div>
              ))}
            </div>
          </div>

          <div className="clientp-panel">
            <div className="clientp-panel-title">My Activity</div>
            <div className="clientp-activity">
              <div className="clientp-stat clientp-stat-blue">
                <div className="clientp-stat-num">{stats.posted}</div>
                <div className="clientp-stat-label">Projects Posted</div>
                <div className="clientp-trend">+18%</div>
              </div>
              <div className="clientp-stat clientp-stat-green">
                <div className="clientp-stat-num">{stats.active}</div>
                <div className="clientp-stat-label">Active Projects</div>
                <div className="clientp-trend">+2</div>
              </div>
              <div className="clientp-stat clientp-stat-amber">
                <div className="clientp-stat-num">{stats.messages}</div>
                <div className="clientp-stat-label">Messages</div>
                <div className="clientp-trend">+12</div>
              </div>
            </div>
          </div>

          <div className="clientp-panel">
            <div className="clientp-panel-title">Account Actions</div>
            <div className="clientp-account-actions">
              <button className="clientp-outline">Change Password</button>
              <button className="clientp-outline danger" onClick={() => { logout(); navigate("/"); }}>
                <LogOut size={16} /> Logout
              </button>
            </div>
          </div>
        </section>
      </section>

      {savedToast && (
        <div className="cp-toast">
          <span className="cp-toast-check">✔</span>
          Changes saved
        </div>
      )}
    </main>
  );
}
