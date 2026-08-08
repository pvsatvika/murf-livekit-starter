import logging
import os
import json
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    llm,
    tokenize
)
from livekit.plugins import deepgram, murf, openai, silero
from src.db import init_db, get_patient, save_patient, delete_patient

logger = logging.getLogger("asha-agent")

load_dotenv(".env.local")
load_dotenv(".env")

# Initialize SQLite database file
init_db()

# Static test ID for the demo caller
USER_ID = "patient_101"

SYSTEM_PROMPT = f"""
IDENTITY & ROLE
You are 'AshaAssist', an AI voice assistant conducting patient intake sessions directly with patients.

DATABASE & MEMORY INSTRUCTIONS
1. User ID for this session is '{USER_ID}'.
2. Before anything else, use `lookup_patient` to check if patient data exists in database.
3. IF RECORD EXISTS:
   - Greet them warmly by name in Devanagari Hindi.
   - Mention their previous condition from memory and ask how they are feeling today.
4. IF NO RECORD EXISTS:
   - Conduct intake: Gather Name, Age band, and Current Symptoms across conversational turns.
   - MANDATORY SEQUENCE: ONLY ask for privacy consent AFTER gathering Name, Age, and Symptoms.
   - CONSENT QUESTION: Ask in Hindi (e.g., "क्या मैं आपकी जानकारी सुरक्षित रख सकती हूँ?").
   - EXECUTION RULE: ONLY invoke `save_patient_data` AFTER the user explicitly confirms consent (e.g., "Yes", "हाँ", "यस").
   - If user denies consent (says NO): Do NOT save anything.

LANGUAGE & SCRIPT
- Write all Hindi in native Devanagari script (नमस्ते).
- Keep spoken responses brief (1-2 sentences).
"""

@llm.function_tool(description="Look up returning patient information from the database")
async def lookup_patient() -> str:
    record = get_patient(USER_ID)
    if record:
        logger.info(f"DB Record found for {USER_ID}: {record}")
        return json.dumps(record)
    logger.info(f"No DB record found for {USER_ID}")
    return "Patient not found."

@llm.function_tool(
    description="STRICT SAFETY MANDATE: Save structured patient intake details (name, age, symptoms) ONLY AFTER the user explicitly grants permission when asked."
)
async def save_patient_data(
    name: str,
    age_band: str,
    ongoing_conditions: str,
    last_triage_outcome: str
) -> str:
    facts = {
        "age_band": age_band,
        "ongoing_conditions": ongoing_conditions,
        "last_triage_outcome": last_triage_outcome
    }
    save_patient(USER_ID, name, "hi", facts)
    logger.info(f"✅ SUCCESSFULLY SAVED PATIENT TO SQLITE: {name}")
    return f"Patient data for {name} saved successfully."

@llm.function_tool(description="Delete saved patient records if requested by user")
async def forget_patient() -> str:
    delete_patient(USER_ID)
    logger.info(f"Deleted records for {USER_ID}")
    return "All stored records for this user have been erased."


server = AgentServer()

def prewarm(proc):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: JobContext):
    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),
        llm=openai.LLM(
            model="llama-3.3-70b-versatile",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
        ),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
            api_key=os.getenv("MURF_API_KEY"),
        ),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    agent = Agent(
        instructions=SYSTEM_PROMPT,
        tools=[lookup_patient, save_patient_data, forget_patient],
    )

    await session.start(
        agent=agent,
        room=ctx.room,
    )

    # Check database on connection
    existing_patient = get_patient(USER_ID)

    if existing_patient:
        name = existing_patient.get("name", "पेशेंट")
        condition = existing_patient.get("facts", {}).get("ongoing_conditions", "तकलीफ")
        await session.say(f"नमस्ते {name}! पिछली बार आपने {condition} के बारे में बताया था। अब आपकी तबियत कैसी है?")
    else:
        await session.say("नमस्ते! मैं आशाअसिस्ट हूँ। क्या आप अपना नाम और उम्र बता सकते हैं?")


if __name__ == "__main__":
    cli.run_app(server)