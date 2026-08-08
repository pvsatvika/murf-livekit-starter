import { AccessToken, RoomServiceClient } from 'livekit-server-sdk';
import { NextResponse } from 'next/server';

export async function POST() {
  try {
    const roomName = `room-${Math.random().toString(36).substring(7)}`;
    const identity = `user-${Math.random().toString(36).substring(7)}`;

    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;
    const wsUrl = process.env.LIVEKIT_URL;

    if (!apiKey || !apiSecret || !wsUrl) {
      return NextResponse.json(
        { error: 'LiveKit environment variables missing in frontend' },
        { status: 500 }
      );
    }

    // 1. Explicitly create the room and dispatch the agent via RoomServiceClient
    const httpUrl = wsUrl.replace('wss://', 'https://').replace('ws://', 'http://');
    const roomService = new RoomServiceClient(httpUrl, apiKey, apiSecret);

    try {
      await roomService.createRoom({
        name: roomName,
        emptyTimeout: 300,
        agents: [
          {
            agentName: 'agent',
          },
        ],
      });
    } catch (e) {
      // Room might already exist or auto-create; safe to proceed
    }

    // 2. Issue the participant token
    const at = new AccessToken(apiKey, apiSecret, {
      identity,
      ttl: '10m',
    });

    at.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
    });

    const participantToken = await at.toJwt();

    return NextResponse.json({
      participantToken,
      serverUrl: wsUrl,
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}