export default function OnboardingImageGrid() {
  // Public images you can drop for guaranteed visibility (no bundling required)
  // Save under: frontend/public/assets/onboarding/
  // Filenames per slot: gallery-1.(jpg|jpeg|png|webp) ... gallery-6.(jpg|jpeg|png|webp)
  const slots = [1, 2, 3, 4, 5, 6];

  const fallback = [
    "https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=900&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1510915361894-db8e1ed0e0d1?q=80&w=900&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1513364776144-60967b0f800f?q=80&w=900&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1519222970733-f546218fa6d7?q=80&w=900&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1526318472351-c75d33c743cf?q=80&w=900&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?q=80&w=900&auto=format&fit=crop",
  ];

  // For each slot, try jpg → jpeg → png → webp, then remote fallback (unique per slot)
  const makeCandidates = (n) => {
    const exts = ["jpg", "jpeg", "png", "webp"];
    const dirs = ["/assets/onboarding", "/assets"]; // support both folders
    const out = [];
    for (const dir of dirs) {
      for (const ext of exts) {
        out.push(`${dir}/gallery-${n}.${ext}`);
      }
    }
    return out;
  };
  // Unique remote images per slot to avoid duplicates when locals are missing
  const remoteBySlot = {
    1: "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?q=80&w=1200&auto=format&fit=crop", // dancer
    2: "https://images.unsplash.com/photo-1526318472351-c75d33c743cf?q=80&w=1200&auto=format&fit=crop", // singer/mic
    3: "https://images.unsplash.com/photo-1513364776144-60967b0f800f?q=80&w=1200&auto=format&fit=crop", // painter
    4: "https://images.unsplash.com/photo-1484704849700-f032a568e944?q=80&w=1200&auto=format&fit=crop", // photographer
    5: "https://images.unsplash.com/photo-1510915361894-db8e1ed0e0d1?q=80&w=1200&auto=format&fit=crop", // musician
    6: "https://images.unsplash.com/photo-1507874457470-272b3c8d8ee2?q=80&w=1200&auto=format&fit=crop", // concert
  };
  const sources = slots.map((n, i) => {
    const localList = makeCandidates(n); // local first
    const primaryList = [...localList, remoteBySlot[n]]; // then unique remote
    return { list: primaryList, fallback: fallback[i % fallback.length] }; // final safety
  });

  const onError = (e, fb) => {
    const img = e.currentTarget;
    const nextStr = img.dataset.next || "";
    const next = nextStr ? nextStr.split("|") : [];
    if (next.length > 0) {
      const candidate = next.shift();
      img.dataset.next = next.join("|");
      img.src = candidate;
    } else {
      if (img.dataset.fallbackApplied) return;
      img.dataset.fallbackApplied = "1";
      img.src = fb;
    }
  };

  return (
    <div className="ob-grid">
      {sources.map(({ list, fallback: fb }, i) => (
        <figure className="ob-card" key={i}>
          <img
            src={list[0]}
            alt={`gallery ${i + 1}`}
            loading="lazy"
            data-next={list.slice(1).join("|")}
            onError={(ev) => onError(ev, fb)}
          />
        </figure>
      ))}
    </div>
  );
}
