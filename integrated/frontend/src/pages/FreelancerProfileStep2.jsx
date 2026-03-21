import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ProfileFormLayout from "../components/ProfileFormLayout.jsx";
import { freelancerService } from "../services/freelancerService.js";
import { useAuth } from "../context/AuthContext.jsx";

const DRAFT_KEY = "fp_draft";
const PIN_ERR_KEY = "fp_error_pin";

export default function FreelancerProfileStep2() {
  const navigate = useNavigate();
  const { user, markProfileCompleted } = useAuth();
  const [basic, setBasic] = useState(null);
  const [form, setForm] = useState({
    bio: "",
    min_budget: "",
    max_budget: "",
    dob: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    try {
      const raw = localStorage.getItem(DRAFT_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        setBasic(parsed);
      }
    } catch {}
  }, []);

  const onField = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

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
        title: `${basic.category || "Artist"} Performer`,
        skills: basic.category || "Artist",
        years: parseInt(basic.experience_years || "0", 10),
        months: parseInt(basic.experience_months || "0", 10),
        min_budget: parseFloat(form.min_budget || "0"),
        max_budget: parseFloat(form.max_budget || "0"),
        bio: form.bio || "",
        category: basic.category || "",
        location: basic.location || "",
        dob: form.dob || "",
        // optional fields supported by backend table
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

  return (
    <ProfileFormLayout step={2}>
      <form className="cp-form cp-slide-in" onSubmit={submitProfile}>
        <label>
          <span>Bio</span>
          <textarea
            rows="4"
            placeholder="Write a short bio..."
            value={form.bio}
            onChange={onField("bio")}
          />
        </label>
        <div className="cp-row">
          <label>
            <span>Minimum Budget</span>
            <input
              type="number"
              min="0"
              placeholder="e.g., 5000"
              value={form.min_budget}
              onChange={onField("min_budget")}
            />
          </label>
          <label>
            <span>Maximum Budget</span>
            <input
              type="number"
              min={form.min_budget || 0}
              placeholder="e.g., 50000"
              value={form.max_budget}
              onChange={onField("max_budget")}
            />
          </label>
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
        <div className="cp-actions">
          <button type="button" className="cp-ghost" onClick={goBack}>← Back</button>
          <button className="cp-primary" disabled={submitting}>
            Submit Profile
          </button>
        </div>
      </form>
    </ProfileFormLayout>
  );
}
