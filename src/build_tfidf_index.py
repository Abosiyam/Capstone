# ============================================================================
# src/build_tfidf_index.py – Build TF-IDF index (no heavy dependencies)
# ============================================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pickle
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

CORPUS_DIR = Path(__file__).parent.parent / 'docs' / 'corpus'
OUTPUT_PATH = Path(__file__).parent.parent / 'artifacts' / 'tfidf_index.pkl'

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def load_documents():
    docs = {}
    for md_file in sorted(CORPUS_DIR.glob('*.md')):
        with open(md_file, 'r', encoding='utf-8') as f:
            docs[md_file.name] = f.read()
    print(f"✅ Loaded {len(docs)} documents")
    return docs


def chunk_text(text, source):
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    buffer = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(buffer) + len(para) > CHUNK_SIZE and buffer:
            chunks.append({'text': buffer.strip(), 'source': source})
            buffer = buffer[-CHUNK_OVERLAP:] + "\n\n" + para
        else:
            buffer = buffer + "\n\n" + para if buffer else para
    if buffer.strip():
        chunks.append({'text': buffer.strip(), 'source': source})
    return chunks


def main():
    print("=" * 60)
    print("Building TF-IDF Index for Head C")
    print("=" * 60)

    docs = load_documents()
    chunks = []
    for source, text in docs.items():
        for c in chunk_text(text, source):
            chunks.append(c)

    print(f"✅ Built {len(chunks)} chunks")

    texts = [c['text'] for c in chunks]

    # TF-IDF with character n-grams for robustness to French/English
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True
    )
    matrix = vectorizer.fit_transform(texts)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'wb') as f:
        pickle.dump({
            'vectorizer': vectorizer,
            'matrix': matrix,
            'chunks': chunks
        }, f)

    print(f"✅ Saved TF-IDF index to {OUTPUT_PATH}")
    print(f"   Matrix shape: {matrix.shape}")
    print(f"   Vocabulary size: {len(vectorizer.vocabulary_)}")


if __name__ == "__main__":
    main()