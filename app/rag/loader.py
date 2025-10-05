import faiss

def load_faiss_index(Path):
    index = faiss.read_index(Path)
    return index