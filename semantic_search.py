# semantic_search.py
import os
import json
import sqlite3
import numpy as np

try:
    import faiss
except Exception:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


STORE_DIR = "gigbridge_store"
INDEX_PATH = os.path.join(STORE_DIR, "freelancer_semantic.faiss")
MODEL_PATH = os.path.join(STORE_DIR, "semantic_model_name.json")  # just to remember config
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


_model = None
_index = None


def _ensure_store():
    if not os.path.exists(STORE_DIR):
        os.makedirs(STORE_DIR, exist_ok=True)


def _get_model():
    global _model
    if _model is not None:
        return _model

    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers not installed. Run: pip install sentence-transformers")

    _ensure_store()

    # keep it stable across runs
    model_name = DEFAULT_MODEL
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, "r", encoding="utf-8") as f:
                model_name = json.load(f).get("model", DEFAULT_MODEL)
        except Exception:
            model_name = DEFAULT_MODEL
    else:
        with open(MODEL_PATH, "w", encoding="utf-8") as f:
            json.dump({"model": model_name}, f)

    _model = SentenceTransformer(model_name)
    return _model


def _embed_texts(texts):
    model = _get_model()
    vecs = model.encode(texts, normalize_embeddings=True)
    return np.asarray(vecs, dtype="float32")


def _make_text_row(row):
    # row = (id, title, skills, bio, tags, category)
    fid = row[0]
    title = row[1] or ""
    skills = row[2] or ""
    bio = row[3] or ""
    tags = row[4] or ""
    cat = row[5] or ""
    text = f"{title}\n{skills}\n{bio}\n{tags}\n{cat}".strip()
    return fid, text


def load_or_build():
    """
    Loads FAISS index from disk if exists. Otherwise builds it from freelancer.db.
    Uses IndexIDMap2 so we can update by freelancer_id later.
    """
    global _index
    if faiss is None:
        raise RuntimeError("faiss not installed. Run: pip install faiss-cpu")

    _ensure_store()

    if os.path.exists(INDEX_PATH):
        _index = faiss.read_index(INDEX_PATH)
        return _index

    # build new
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT freelancer_id,
               COALESCE(title,''),
               COALESCE(skills,''),
               COALESCE(bio,''),
               COALESCE(tags,''),
               COALESCE(category,'')
        FROM freelancer_profile
    """)
    rows = cur.fetchall()
    conn.close()

    pairs = [_make_text_row(r) for r in rows if r and r[0] is not None]
    if not pairs:
        # empty index
        base = faiss.IndexFlatIP(384)
        _index = faiss.IndexIDMap2(base)
        faiss.write_index(_index, INDEX_PATH)
        return _index

    ids = np.array([p[0] for p in pairs], dtype="int64")
    texts = [p[1] for p in pairs]

    vecs = _embed_texts(texts)
    dim = vecs.shape[1]

    base = faiss.IndexFlatIP(dim)
    _index = faiss.IndexIDMap2(base)
    _index.add_with_ids(vecs, ids)

    faiss.write_index(_index, INDEX_PATH)
    return _index


def upsert_freelancer(freelancer_id: int):
    """
    Remove old vector for freelancer_id (if present) and add new one.
    Call this whenever freelancer_profile is updated.
    """
    global _index
    if _index is None:
        load_or_build()

    fid = int(freelancer_id)

    # pull fresh profile text
    conn = sqlite3.connect("freelancer.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT freelancer_id,
               COALESCE(title,''),
               COALESCE(skills,''),
               COALESCE(bio,''),
               COALESCE(tags,''),
               COALESCE(category,'')
        FROM freelancer_profile
        WHERE freelancer_id=?
    """, (fid,))
    row = cur.fetchone()
    conn.close()

    # if profile not found, remove from index
    remove_ids = np.array([fid], dtype="int64")
    _index.remove_ids(remove_ids)

    if not row:
        faiss.write_index(_index, INDEX_PATH)
        return

    _, text = _make_text_row(row)
    vec = _embed_texts([text])

    _index.add_with_ids(vec, np.array([fid], dtype="int64"))
    faiss.write_index(_index, INDEX_PATH)


def semantic_search(query: str, top_k: int = 20):
    """
    Returns list of freelancer_ids ranked by semantic similarity.
    """
    global _index
    if _index is None:
        load_or_build()

    q = (query or "").strip()
    if not q:
        return []

    qvec = _embed_texts([q])
    D, I = _index.search(qvec, top_k)

    ids = [int(x) for x in I[0] if int(x) != -1]
    return ids