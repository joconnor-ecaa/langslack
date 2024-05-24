import logging

from slack_bolt.async_app import AsyncApp

logging.basicConfig(level=logging.DEBUG)
app = AsyncApp()


@app.command("/hello-bolt-python")
async def hello(body, ack):
    user_id = body["user_id"]
    await ack(f"Hi <@{user_id}>!")


from fastapi import FastAPI, Request

api = FastAPI()

from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

app_handler = AsyncSlackRequestHandler(app)


@api.post("/slack/events")
async def endpoint(req: Request):
    return await app_handler.handle(req)


@app.event("message")
def event_message(body, say, logger):
    logger.info(body)
    message = body["event"]["text"]
    docs = []
    if body["event"]["channel_type"] == "im":
        conversation_id = body["event"]["user"]
    else:
        conversation_id = body["event"]["channel"]
    client = MessageClient.objects.get_or_create(conversation_id=conversation_id)[0]
    history = client.get_history()
    if history:
        docs = [Document(page_content=history)]
    chain = load_qa_chain(OpenAIChat(model_name="gpt-4"), chain_type="stuff")
    try:
        result = chain(
            {"input_documents": docs, "question": message}, return_only_outputs=True
        )
    except:
        result = {"output_text": "We are very busy right now :( Please try again."}
    response = result["output_text"].strip()
    MessageEntry.objects.create(
        question=message, answer=result["output_text"], client=client
    )
    say(response)
