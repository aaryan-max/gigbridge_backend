import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ProfileFormLayout from "../components/ProfileFormLayout.jsx";
import { freelancerService } from "../services/freelancerService.js";
import { useAuth } from "../context/AuthContext.jsx";

const DRAFT_KEY = "fp_draft";
const PIN_ERR_KEY = "fp_error_pin";

function getPricingType(category) {
  const hourly = ["DJ", "Singer", "Anchor", "Band / Live Music", "Dancer", "Magician / Entertainer"];
  const perPerson = ["Makeup Artist", "Mehendi Artist"];
  const packageType = ["Photographer", "Videographer", "Choreographer", "Artist"];
  const project = ["Decorator", "Wedding Planner", "Event Organizer"];

  if (hourly.includes(category)) return "HOURLY";
  if (perPerson.includes(category)) return "PER_PERSON";
  if (packageType.includes(category)) return "PACKAGE";
  if (project.includes(category)) return "PROJECT";
  return "HOURLY"; // Default
}

export default function FreelancerProfileStep2() {
  const navigate = useNavigate();
  const { user, markProfileCompleted } = useAuth();
  const [basic, setBasic] = useState(null);
  
  const [form, setForm] = useState({
    title: "",
    skills: "",
    bio: "",
    dob: "",
  });

  const [pricing, setPricing] = useState({
    type: "HOURLY",
    hourlyRate: "",
    hasOvertime: false,
    overtimeRate: "",
    perPersonRate: "",
    projectPrice: 25000,
    description: "",
    services: "",
  });

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    try {
      const raw = localStorage.getItem(DRAFT_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        setBasic(parsed);
        if (parsed.category) {
          setPricing((prev) => ({
            ...prev,
            type: getPricingType(parsed.category)
          }));
        }
      }
    } catch {}
  }, []);

  const onField = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  
  const onPricingField = (k) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setPricing((p) => ({ ...p, [k]: val }));
  };

  const goBack = () => navigate("/freelancer/create-profile/step-1");

  const submitProfile = async (e) => {
    e.preventDefault();
    if (!basic) {
      setError("Please complete Step 1 first.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const payload = {
        freelancer_id: user?.id,
        title: form.title || `${basic.category || "Artist"} Performer`,
        skills: form.skills || basic.category || "Artist",
        years: parseInt(basic.experience_years || "0", 10),
        months: parseInt(basic.experience_months || "0", 10),
        pricing_type: pricing.type,
        pricing_details: JSON.stringify(pricing),
        bio: form.bio || "",
        category: basic.category || "",
        location: basic.location || "",
        dob: form.dob || "",
        pincode: basic.pincode || "",
      };
      
      const res = await freelancerService.createProfile(payload);
      console.log("Profile response:", res);
      if (res && res.success) {
        localStorage.removeItem(DRAFT_KEY);
        localStorage.removeItem(PIN_ERR_KEY);
        markProfileCompleted();
        navigate("/artist/dashboard", { replace: true });
      } else {
        console.log("Profile error:", res);
        const msg = res?.msg || "Failed to create profile";
        if (msg.includes("pincode")) {
          localStorage.setItem(PIN_ERR_KEY, msg);
          navigate("/freelancer/create-profile/step-1");
        } else {
          setError(msg);
        }
      }
    } catch (err) {
      const msg = err?.message || "Network error";
      if (msg.includes("pincode")) {
        localStorage.setItem(PIN_ERR_KEY, msg);
        navigate("/freelancer/create-profile/step-1");
      } else {
        setError(msg);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const renderPricingUI = () => {
    switch (pricing.type) {
      case "HOURLY":
        return (
          <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '16px' }}>
            <label>
              <span style={{ fontWeight: 600, color: '#1e293b' }}>Hourly Rate (₹/hour)</span>
              <input type="number" min="0" value={pricing.hourlyRate} onChange={onPricingField("hourlyRate")} />
            </label>
            <label style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '8px', cursor: 'pointer', marginTop: '6px' }}>
              <input type="checkbox" checked={pricing.hasOvertime} onChange={onPricingField("hasOvertime")} style={{ width: 'auto', height: 'auto', margin: 0 }} />
              <span style={{ margin: 0, fontSize: '14px', color: '#475569' }}>Set overtime rate?</span>
            </label>
            {pricing.hasOvertime && (
              <label className="fade-in" style={{ marginTop: '8px' }}>
                <span style={{ fontWeight: 600, color: '#1e293b' }}>Overtime Rate (₹/hour)</span>
                <input type="number" min="0" value={pricing.overtimeRate} onChange={onPricingField("overtimeRate")} />
              </label>
            )}
          </div>
        );
      case "PER_PERSON":
        return (
          <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '16px' }}>
            <label>
              <span style={{ fontWeight: 600, color: '#1e293b' }}>Per Person Rate (₹/person)</span>
              <input type="number" min="0" value={pricing.perPersonRate} onChange={onPricingField("perPersonRate")} />
            </label>
          </div>
        );
      case "PACKAGE":
        return (
          <div className="fade-in" style={{ padding: '16px', background: '#eef6ff', borderRadius: '12px', color: '#2563eb', fontWeight: '500', textAlign: 'center', marginBottom: '16px', border: '1px solid #bfdbfe' }}>
            Packages will be managed separately
          </div>
        );
      case "PROJECT":
        return (
          <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '12px', background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '16px' }}>
            <label>
              <span style={{ fontWeight: 600, color: '#1e293b' }}>Starting Project Price (₹)</span>
              <input type="number" min="0" value={pricing.projectPrice} onChange={onPricingField("projectPrice")} />
            </label>
            <label>
              <span style={{ fontWeight: 600, color: '#1e293b' }}>Work Description</span>
              <textarea rows="3" value={pricing.description} onChange={onPricingField("description")} />
            </label>
            <label>
              <span style={{ fontWeight: 600, color: '#1e293b' }}>Services Included</span>
              <input type="text" placeholder="Comma-separated (optional)" value={pricing.services} onChange={onPricingField("services")} />
            </label>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <ProfileFormLayout step={2}>
      <form className="cp-form cp-slide-in" onSubmit={submitProfile}>
        <label>
          <span>Title</span>
          <input
            type="text"
            placeholder="e.g. Professional Wedding Photographer / DJ for Events"
            value={form.title}
            onChange={onField("title")}
          />
        </label>
        
        <label>
          <span>Skills</span>
          <input
            type="text"
            placeholder="e.g. Video Editing, Lighting, Drone (comma separated)"
            value={form.skills}
            onChange={onField("skills")}
          />
        </label>

        <label>
          <span>Bio</span>
          <textarea
            rows="4"
            placeholder="Write a short bio..."
            value={form.bio}
            onChange={onField("bio")}
          />
        </label>

        <div style={{ marginTop: '24px', marginBottom: '8px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#0f172a', marginBottom: '12px' }}>Pricing Information</h3>
          {renderPricingUI()}
        </div>

        <label>
          <span>Date of Birth</span>
          <input
            type="date"
            value={form.dob}
            onChange={onField("dob")}
          />
        </label>
        
        {error && (
          <div style={{ color: "#dc2626", fontSize: 12 }}>
            {error}
          </div>
        )}
        
        <div className="cp-actions" style={{ marginTop: '24px' }}>
          <button type="button" className="cp-ghost" onClick={goBack}>← Back</button>
          <button className="cp-primary" disabled={submitting}>
            Submit Profile
          </button>
        </div>
      </form>
    </ProfileFormLayout>
  );
}
