from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2

app = FastAPI()

# DB connection
conn = psycopg2.connect(
    database="careerflow",
    user="careeruser",
    password="StrongPassword123",
    host="localhost",
    port="5432"
)

class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(req: ChatRequest):

    msg = req.message.lower()

    cur = conn.cursor()

    # search keyword match
    cur.execute(
        "SELECT response FROM chatbot_responses WHERE %s ILIKE '%' || keyword || '%'",
        (msg,)
    )

    result = cur.fetchone()

    if result:
        return {"reply": result[0]}

    # fallback response
    cur.execute("SELECT response FROM chatbot_responses WHERE keyword='default'")
    default_reply = cur.fetchone()[0]

    return {"reply": default_reply}