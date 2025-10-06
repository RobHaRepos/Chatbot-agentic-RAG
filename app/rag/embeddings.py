from sentence_transformers import SentenceTransformer

def define_model_for_embeddings(model_name:str):
    return SentenceTransformer(model_name)

def embed_texts(text: str, model_embedding):
    embeddings = model_embedding.encode(text)
    return embeddings