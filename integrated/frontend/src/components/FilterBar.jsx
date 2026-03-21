import React from 'react';

const VALID_CATEGORIES = [
  "Photographer", "Videographer", "DJ", "Singer", "Dancer",
  "Anchor", "Makeup Artist", "Mehendi Artist", "Decorator",
  "Wedding Planner", "Choreographer", "Band / Live Music",
  "Magician / Entertainer", "Artist", "Event Organizer"
];

export default function FilterBar({
  selectedCategories,
  onToggleCategory,
  onReset
}) {
  return (
    <aside className="ba-filters-modern">
      <div className="ba-f-title">Filters</div>
      <div className="ba-filter-sec">
        <div className="ba-sec-title">Specialty Categories</div>
        <div className="ba-pills-modern">
          {VALID_CATEGORIES.map(cat => (
             <button
              key={cat}
              className={`chip-modern ${selectedCategories.includes(cat) ? "active" : ""}`}
              onClick={() => onToggleCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>
      <button className="ba-clear-modern" onClick={onReset}>
        Reset Filters
      </button>
    </aside>
  );
}
