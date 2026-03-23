import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import ProfileFormLayout from "../components/ProfileFormLayout.jsx";

const VALID_CATEGORIES = [
  "Photographer",
  "Videographer",
  "DJ",
  "Singer",
  "Dancer",
  "Anchor",
  "Makeup Artist",
  "Mehendi Artist",
  "Decorator",
  "Wedding Planner",
  "Choreographer",
  "Band / Live Music",
  "Magician / Entertainer",
  "Artist",
  "Event Organizer",
];

const DRAFT_KEY = "fp_draft";
const PIN_ERR_KEY = "fp_error_pin";

export default function FreelancerProfileStep1() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    category: "",
    location: "",
    pincode: "",
    experience_years: "",
  });
  const [pinErr, setPinErr] = useState("");

  useEffect(() => {
    try {
      const raw = localStorage.getItem(DRAFT_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        setForm((f) => ({ ...f, ...parsed }));
      }
      const perr = localStorage.getItem(PIN_ERR_KEY);
      if (perr) setPinErr(perr);
    } catch {}
  }, []);

  const onField = (k) => (e) => {
    const val = e.target.value;
    setForm((f) => ({ ...f, [k]: val }));
    if (k === "pincode") {
      setPinErr("");
      localStorage.removeItem(PIN_ERR_KEY);
    }
  };

  const isValidPin = useMemo(() => /^\d{6}$/.test(form.pincode || ""), [form.pincode]);
  const yearsValid = useMemo(() => /^(?:\d|[1-3]\d|40)$/.test(form.experience_years || "0"), [form.experience_years]);

  const canContinue =
    form.category &&
    form.location &&
    isValidPin &&
    yearsValid;

  const continueToStep2 = (e) => {
    e.preventDefault();
    if (!canContinue) return;
    localStorage.setItem(DRAFT_KEY, JSON.stringify(form));
    navigate("/freelancer/create-profile/step-2");
  };

  return (
    <ProfileFormLayout step={1}>
      <form className="cp-form cp-slide-in" onSubmit={continueToStep2}>
        <label>
          <span>Category *</span>
          <select
            value={form.category}
            onChange={onField("category")}
            required
          >
            <option value="">Select a category</option>
            {VALID_CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>

        <div className="cp-row">
          <label>
            <span>Location *</span>
            <input
              type="text"
              placeholder="City, State"
              value={form.location}
              onChange={onField("location")}
              required
            />
          </label>
          <label>
            <span>Pin Code *</span>
            <input
              type="number"
              placeholder="6-digit pincode"
              value={form.pincode}
              onChange={onField("pincode")}
              required
            />
            {(!isValidPin || pinErr) && (
              <div style={{ color: "#dc2626", fontSize: 12, marginTop: 4 }}>
                {pinErr || "Enter valid pincode"}
              </div>
            )}
          </label>
        </div>

        <label>
          <span>Years of Experience</span>
          <input
            type="number"
            min="0"
            max="40"
            placeholder="0–40"
            value={form.experience_years}
            onChange={onField("experience_years")}
          />
        </label>

        <button className="cp-primary">
          Continue <span className="cp-arrow">→</span>
        </button>
      </form>
    </ProfileFormLayout>
  );
}
