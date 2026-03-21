export default function CategoryCard({ icon, label, selected, onClick }) {
  return (
    <button
      type="button"
      className={`cat-card ${selected ? "cat-selected" : ""}`}
      onClick={onClick}
    >
      <div className="cat-ico">{icon}</div>
      <div className="cat-label">{label}</div>
    </button>
  );
}
