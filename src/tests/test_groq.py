import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": "Ti si pomoćni asistent za studente."},
        {"role": "user", "content": "Koji su rokovi za upis godine na ETF?"}
    ]
)

print(response.choices[0].message.content)