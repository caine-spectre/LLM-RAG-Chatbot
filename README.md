## Chiba Guide Chatbot Backend

## Overview

  This project is LLM RAG Chatbot using Langchain. I used Pinecone for vectorDB, FastAPI for Backend. GPT-4o for OpenAI model, Langchain for LLM Integration.

## Requirements

- Python 3.12.3

## Setup

1. run the application. <br />
Create a virtual environment to run Python. 
Refer to the following link.
 <br />
https://qiita.com/futakuchi0117/items/6030458a96f62cb64d37<br />
https://qiita.com/fiftystorm36/items/b2fd47cf32c7694adc2e

Install the required Python packages.
```
pip install -r requirements.txt
```

3. create a `.env` file in the root directory of your project and set the `SECRET_KEY` and `OPENAI_API_KEY`.
```
SECRET_KEY= your private key
OPENAI_API_KEY= your private key
```

## How to execute.
```
py app.py
````

Open a browser and go to ``http://localhost:5000`` to test your application.
