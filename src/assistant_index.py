# ============================================================================
# src/assistant_index.py – Retrieval Index for Head C (fastembed version)
# ============================================================================

import json
import re
from pathlib import Path
from typing import List, Dict
import numpy as np

from fastembed import TextEmbedding
import faiss

# ---------- Paths ----------
CORPUS_DIR = Path(__file__).parent.parent / 'docs' / 'corpus'
INDEX_DIR = Path(__file__).parent.parent / 'artifacts' / 'faiss_index'
INDEX_PATH = INDEX_DIR / 'index.faiss'
CHUNKS_PATH = INDEX_DIR / 'chunks.json'

# ---------- Model ----------
EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def load_documents() -> Dict[str, str]:
    """Load all markdown files from the corpus directory."""
    if not CORPUS_DIR.exists():
        raise FileNotFoundError(f"Corpus directory not found: {CORPUS_DIR}")

    docs = {}
    for md_file in sorted(CORPUS_DIR.glob('*.md')):
        with open(md_file, 'r', encoding='utf-8') as f:
            docs[md_file.name] = f.read()

    print(f"✅ Loaded {len(docs)} documents: {list(docs.keys())}")
    return docs


def chunk_text(text: str, source: str) -> List[Dict]:
    """Split text into overlapping chunks by paragraph boundaries."""
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    buffer = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(buffer) + len(para) > CHUNK_SIZE and buffer:
            chunks.append({
                'text': buffer.strip(),
                'source': source
            })
            buffer = buffer[-CHUNK_OVERLAP:] + "\n\n" + para
        else:
            buffer = buffer + "\n\n" + para if buffer else para

    if buffer.strip():
        chunks.append({
            'text': buffer.strip(),
            'source': source
        })

    return chunks


def build_chunks(docs: Dict[str, str]) -> List[Dict]:
    """Build chunks from all documents, adding section metadata."""
    all_chunks = []
    for source, text in docs.items():
        chunks = chunk_text(text, source)
        for i, chunk in enumerate(chunks):
            chunk['chunk_id'] = f"{source.replace('.md', '')}_chunk_{i:03d}"
        all_chunks.extend(chunks)

    print(f"✅ Built {len(all_chunks)} chunks from {len(docs)} documents")
    return all_chunks


def build_index(chunks: List[Dict]) -> None:
    """Embed chunks and build FAISS index."""
    print(f"\n🔧 Loading embedding model: {EMBEDDING_MODEL}")
    model = TextEmbedding(model_name=EMBEDDING_MODEL)

    print(f"🔧 Embedding {len(chunks)} chunks...")
    texts = [c['text'] for c in chunks]
    embeddings = np.array(list(model.embed(texts)), dtype='float32')

    # Normalise for cosine similarity
    faiss.normalize_L2(embeddings)

    # Build index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # Save
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))

    with open(CHUNKS_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            'model': EMBEDDING_MODEL,
            'dimension': dim,
            'chunk_count': len(chunks),
            'chunks': chunks
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Index saved to {INDEX_PATH}")
    print(f"✅ Chunks saved to {CHUNKS_PATH}")
    print(f"   Dimension: {dim}")
    print(f"   Chunk count: {len(chunks)}")


def main():
    print("=" * 60)
    print("Head C – Building Retrieval Index (fastembed)")
    print("=" * 60)

    docs = load_documents()
    chunks = build_chunks(docs)
    build_index(chunks)

    print("\n✅ Index build complete!")


if __name__ == "__main__":
    main()