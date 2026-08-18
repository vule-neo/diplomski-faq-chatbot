from sentence_transformers import SentenceTransformer
import chromadb

questions=["kada je rok za predaju dokumenata za upis?", "Koji je broj racuna fakulteta?",
            "Koja je procedura za ponistavanje ispita", "Kada je rok za upis?",
            "koja je cena skolarine za SI smer?"]

sentence_trans = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
chroma_client = chromadb.Client()
chroma_collection = chroma_client.create_collection(name="ccollection")

ids_list = ["id1", "id2", "id3", "id4", "id5"]

question_embeddings = sentence_trans.encode(questions).tolist()
print(f'QUESTION EMBEDDINGS = {question_embeddings}')
chroma_collection.add(
    documents=questions,
    embeddings=question_embeddings,
    ids=ids_list
)

test_query = "Dokle treba predati papire da bih se upisao?"
test_embedding = sentence_trans.encode([test_query]).tolist()

results = chroma_collection.query(
    query_embeddings=test_embedding,
    n_results=3
)

print(f"upit: {test_query}\n")
for doc, distance in zip(results["documents"][0], results["distances"][0]):
    print(f"{distance:.4f}  {doc}")
