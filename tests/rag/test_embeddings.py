from app.rag.embeddings import define_model_for_embeddings, embed_texts
from app.config import MODEL_NAME_EMBEDDING

def test_define_model_for_embeddings():
    model = define_model_for_embeddings(MODEL_NAME_EMBEDDING)
    assert model is not None
    
def test_model_embedding():
    model = define_model_for_embeddings(MODEL_NAME_EMBEDDING)
    text = "This is a test sentence."
    embeddings = embed_texts(text, model)
    assert embeddings is not None