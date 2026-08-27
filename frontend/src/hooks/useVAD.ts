import { useEffect, useRef, useState, useCallback } from 'react';
import type { Socket } from 'socket.io-client';
import type { VADState } from '../types/sfu';

export interface UseVADOptions {
  localStream: MediaStream | null;
  socket: Socket | null;
  roomCode: string;
}

export const useVAD = ({ localStream, socket, roomCode }: UseVADOptions) => {
  const [vadState, setVadState] = useState<VADState>({
    activeSpeakerSid: null,
    activeSpeakerName: null,
    audioLevelDbfs: -100,
    audioLevelPercent: 0,
    isSpeaking: false,
  });

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Initialize WebAudio Analyzer for VAD Energy Calculation
  useEffect(() => {
    if (!localStream) return;

    const audioTracks = localStream.getAudioTracks();
    if (audioTracks.length === 0) return;

    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtx();
      const source = ctx.createMediaStreamSource(localStream);
      const analyser = ctx.createAnalyser();

      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.5;
      source.connect(analyser);

      audioContextRef.current = ctx;
      analyserRef.current = analyser;

      const pcmData = new Float32Array(analyser.fftSize);

      const processAudio = () => {
        if (!analyserRef.current) return;

        analyserRef.current.getFloatTimeDomainData(pcmData);
        let sumSquares = 0;
        for (let i = 0; i < pcmData.length; i++) {
          sumSquares += pcmData[i] * pcmData[i];
        }

        const rms = Math.sqrt(sumSquares / pcmData.length);
        const dbfs = rms > 0 ? 20 * Math.log10(rms) : -100;
        const normalized = dbfs <= -90 ? 0 : dbfs >= 0 ? 100 : Math.round(((dbfs + 90) / 90) * 100);
        const isSpeaking = dbfs > -45;

        setVadState((prev) => ({
          ...prev,
          audioLevelDbfs: Math.round(dbfs),
          audioLevelPercent: normalized,
          isSpeaking,
        }));

        if (socket && isSpeaking && Math.random() < 0.2) {
          socket.emit('sfu_vad_energy', {
            room_code: roomCode,
            audio_level_dbfs: dbfs,
          });
        }

        animationFrameRef.current = requestAnimationFrame(processAudio);
      };

      processAudio();
    } catch (err) {
      console.warn('VAD AudioContext initialization error:', err);
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, [localStream, socket, roomCode]);

  // Listen for SFU active speaker broadcasts
  useEffect(() => {
    if (!socket) return;

    const handleActiveSpeakerChange = (data: { sid: string; display_name: string }) => {
      setVadState((prev) => ({
        ...prev,
        activeSpeakerSid: data.sid,
        activeSpeakerName: data.display_name,
      }));
    };

    socket.on('sfu_active_speaker_change', handleActiveSpeakerChange);

    return () => {
      socket.off('sfu_active_speaker_change', handleActiveSpeakerChange);
    };
  }, [socket]);

  return vadState;
};
