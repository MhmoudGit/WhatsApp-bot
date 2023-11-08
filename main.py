import os
from typing import Any
from fastapi import FastAPI, Form, HTTPException, Request, Response
from dotenv import load_dotenv
import httpx
from heyoo import WhatsApp

# Env Variables
load_dotenv()
API_URL: str | None = os.getenv("API_URL")
API_TOKEN: str | None = os.getenv("API_TOKEN")
WHATSAPP_TOKEN: str | None = os.getenv("WHATSAPP_TOKEN")
TEST_NUMBER: str | None = os.getenv("TEST_NUMBER")
HUB_TOKEN: str | None = os.getenv("HUB_TOKEN")


# Whatsapp Handler
messenger = WhatsApp(WHATSAPP_TOKEN, phone_number_id=TEST_NUMBER)

app = FastAPI()


# normal api route for local usage
@app.post("/chat")
async def start_chat(data: str = Form(...)) -> Any:
    res: Any = await query(API_URL, API_TOKEN, data)
    return res["generated_text"]


# Hugging Face Model Query
async def query(url: str, token: str, data) -> Any:
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response: Response = await client.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(
            400,
            detail={
                "res_status_code": response.status_code,
            },
        )


# ---------------------------------------WhatsApp--------------------------------------


# webhook verification
@app.get("/webhook")
async def webhook_verify(request: Request) -> Any:
    params = request.query_params
    if params["hub.mode"] == "subscribe" and params["hub.verify_token"] == HUB_TOKEN:
        challenge: str = params["hub.challenge"]
        return Response(challenge)
    else:
        raise HTTPException(status_code=401, detail="bad request")


@app.post("/webhook")
async def whatsapp(req: Request) -> Any:
    data = await req.json()
    changed_field: str = messenger.changed_field(data)
    if changed_field == "messages":
        new_message: str | None = messenger.get_mobile(data)
        if new_message:
            mobile: str | None = messenger.get_mobile(data)
            message_type: str | None = messenger.get_message_type(data)
            if message_type == "text":
                message: str | None = messenger.get_message(data)
                res: Any = await query(API_URL, API_TOKEN, message)
                messenger.send_message(res["generated_text"], mobile)
