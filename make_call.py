import asyncio
import os
import sys
from dotenv import load_dotenv
from livekit import api

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
SIP_TRUNK_ID = os.getenv("SIP_TRUNK_ID", "ST_YOUR_SIP_TRUNK_ID")


async def trigger_outbound_call(phone_number: str):
    lkapi = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )

    room_name = f"outbound-call-{phone_number.replace('+', '').strip()}"

    print(f"?? Initiating outbound call to {phone_number} in room: {room_name}...")

    try:
        sip_participant = await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=SIP_TRUNK_ID,
                sip_call_to=phone_number,
                room_name=room_name,
                participant_identity=f"phone_{phone_number}",
            )
        )
        print(f"? Call initiated successfully! Participant ID: {sip_participant.participant_id}")
    except Exception as e:
        print(f"? Failed to place call: {e}")
        print("\nNote: For live phone calls, ensure a SIP Outbound Trunk is configured in LiveKit Console connected to Twilio.")
    finally:
        await lkapi.aclose()


if __name__ == "__main__":
    target_number = sys.argv[1] if len(sys.argv) > 1 else "+919999999999"
    asyncio.run(trigger_outbound_call(target_number))
