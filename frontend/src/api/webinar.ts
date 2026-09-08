import client from './client';

export const askWebinarQuestion = async (roomCode: string, question: string, speakerName: string) => {
  const response = await client.post('/api/webinar/qa/ask', {
    room_code: roomCode,
    question,
    speaker_name: speakerName,
  });
  return response.data;
};

export const createBreakoutRooms = async (mainRoomCode: string, participants: string[], numRooms = 2) => {
  const response = await client.post('/api/webinar/breakout/create', {
    main_room_code: mainRoomCode,
    participants,
    num_rooms: numRooms,
  });
  return response.data;
};
