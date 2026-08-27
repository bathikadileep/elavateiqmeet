import { useState, useEffect, useRef, useCallback } from 'react';
import { useSocket } from '../contexts/SocketContext';
import { useAuth } from '../hooks/useAuth';
import type { PeerStream, PeerMediaState } from '../types/webrtc';

const ICE_SERVERS: RTCConfiguration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'stun:stun2.l.google.com:19302' },
    { urls: 'stun:stun3.l.google.com:19302' },
    { urls: 'stun:stun4.l.google.com:19302' },
  ],
};

export const useWebRTC = (roomCode: string) => {
  const { user } = useAuth();
  const { socket, isConnected, joinRoom, leaveRoom } = useSocket();

  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [peers, setPeers] = useState<PeerStream[]>([]);
  const [isAudioMuted, setIsAudioMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [handRaised, setHandRaised] = useState(false);
  const [mediaError, setMediaError] = useState<string | null>(null);

  const peerConnections = useRef<Record<string, RTCPeerConnection>>({});
  const pendingCandidatesQueue = useRef<Record<string, RTCIceCandidateInit[]>>({});
  const localStreamRef = useRef<MediaStream | null>(null);
  const screenStreamRef = useRef<MediaStream | null>(null);

  // Initialize Local Media Stream (Camera & Microphone) with Ultra-Low Latency Settings
  const initLocalStream = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { max: 1280, ideal: 854 },
          height: { max: 720, ideal: 480 },
          frameRate: { max: 30, ideal: 24 },
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000,
        },
      });
      localStreamRef.current = stream;
      setLocalStream(stream);
      setMediaError(null);
      return stream;
    } catch (err) {
      console.warn('Camera/Microphone access fallback:', err);
      setMediaError('Unable to access camera or microphone. Operating in view-only mode.');
      return null;
    }
  }, []);

  // Flush pending ICE candidates once remote description is set
  const processPendingCandidates = async (peerSid: string, pc: RTCPeerConnection) => {
    const queue = pendingCandidatesQueue.current[peerSid];
    if (queue && queue.length > 0) {
      for (const candidate of queue) {
        try {
          await pc.addIceCandidate(new RTCIceCandidate(candidate));
        } catch (err) {
          console.error('Failed adding queued ICE candidate:', err);
        }
      }
      pendingCandidatesQueue.current[peerSid] = [];
    }
  };

  // Join Room & Setup WebRTC Signaling Handlers
  useEffect(() => {
    if (!socket || !isConnected || !roomCode) return;

    initLocalStream().then(() => {
      joinRoom(roomCode);
    });

    // Create RTCPeerConnection for a new peer
    const createPeerConnection = (peerSid: string, peerName: string) => {
      if (peerConnections.current[peerSid]) {
        return peerConnections.current[peerSid];
      }

      const pc = new RTCPeerConnection(ICE_SERVERS);

      // Add local tracks to peer connection
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach((track) => {
          pc.addTrack(track, localStreamRef.current!);
        });
      }

      // Receive remote tracks and accumulate audio + video tracks safely
      pc.ontrack = (event) => {
        setPeers((prev) => {
          const existingPeer = prev.find((p) => p.sid === peerSid);
          if (existingPeer && existingPeer.stream) {
            const currentStream = existingPeer.stream;
            if (!currentStream.getTracks().some((t) => t.id === event.track.id)) {
              currentStream.addTrack(event.track);
            }
            const updatedStream = new MediaStream(currentStream.getTracks());
            return prev.map((p) => (p.sid === peerSid ? { ...p, stream: updatedStream } : p));
          }

          const newStream = event.streams[0] || new MediaStream([event.track]);
          return [
            ...prev,
            {
              sid: peerSid,
              name: peerName,
              stream: newStream,
              isLocal: false,
              isAudioMuted: false,
              isVideoOff: false,
              isScreenSharing: false,
              handRaised: false,
            },
          ];
        });
      };

      // Send local ICE candidates to remote peer via Socket.IO
      pc.onicecandidate = (event) => {
        if (event.candidate) {
          socket.emit('webrtc_ice_candidate', {
            target_sid: peerSid,
            candidate: event.candidate,
          });
        }
      };

      peerConnections.current[peerSid] = pc;
      return pc;
    };

    // Socket Event: New User Joined -> Send WebRTC SDP Offer
    const handleUserJoined = async (data: { sid: string; display_name: string }) => {
      if (data.sid === socket.id) return;

      const pc = createPeerConnection(data.sid, data.display_name || 'Peer');
      try {
        const offer = await pc.createOffer({
          offerToReceiveAudio: true,
          offerToReceiveVideo: true,
        });
        await pc.setLocalDescription(offer);

        socket.emit('webrtc_offer', {
          target_sid: data.sid,
          sdp: offer,
        });
      } catch (err) {
        console.error('Failed to create WebRTC offer:', err);
      }
    };

    // Socket Event: Received WebRTC SDP Offer -> Send WebRTC SDP Answer
    const handleWebRTCOffer = async (data: { sender_sid: string; sender_name: string; sdp: RTCSessionDescriptionInit }) => {
      const pc = createPeerConnection(data.sender_sid, data.sender_name || 'Peer');
      try {
        await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
        await processPendingCandidates(data.sender_sid, pc);

        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);

        socket.emit('webrtc_answer', {
          target_sid: data.sender_sid,
          sdp: answer,
        });
      } catch (err) {
        console.error('Failed to handle WebRTC offer:', err);
      }
    };

    // Socket Event: Received WebRTC SDP Answer -> Complete Handshake
    const handleWebRTCAnswer = async (data: { sender_sid: string; sdp: RTCSessionDescriptionInit }) => {
      const pc = peerConnections.current[data.sender_sid];
      if (pc) {
        try {
          await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
          await processPendingCandidates(data.sender_sid, pc);
        } catch (err) {
          console.error('Failed to handle WebRTC answer:', err);
        }
      }
    };

    // Socket Event: Received ICE Candidate -> Add Candidate or Queue if Remote Description pending
    const handleWebRTCCandidate = async (data: { sender_sid: string; candidate: RTCIceCandidateInit }) => {
      const pc = peerConnections.current[data.sender_sid];
      if (pc && pc.remoteDescription && pc.remoteDescription.type) {
        try {
          await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
        } catch (err) {
          console.error('Failed to add ICE candidate:', err);
        }
      } else {
        if (!pendingCandidatesQueue.current[data.sender_sid]) {
          pendingCandidatesQueue.current[data.sender_sid] = [];
        }
        pendingCandidatesQueue.current[data.sender_sid].push(data.candidate);
      }
    };

    // Socket Event: Remote Peer Left -> Cleanup Connection & Stream
    const handleUserLeft = (data: { sid: string }) => {
      if (peerConnections.current[data.sid]) {
        peerConnections.current[data.sid].close();
        delete peerConnections.current[data.sid];
      }
      setPeers((prev) => prev.filter((p) => p.sid !== data.sid));
    };

    // Socket Event: Remote Peer Media State Changed (mute, video off, screen share)
    const handleMediaStateChanged = (data: PeerMediaState) => {
      setPeers((prev) =>
        prev.map((p) =>
          p.sid === data.sid
            ? {
                ...p,
                isAudioMuted: data.is_audio_muted,
                isVideoOff: data.is_video_off,
                isScreenSharing: data.is_screen_sharing,
                handRaised: data.hand_raised,
              }
            : p
        )
      );
    };

    socket.on('user_joined', handleUserJoined);
    socket.on('webrtc_offer', handleWebRTCOffer);
    socket.on('webrtc_answer', handleWebRTCAnswer);
    socket.on('webrtc_ice_candidate', handleWebRTCCandidate);
    socket.on('user_left', handleUserLeft);
    socket.on('media_state_changed', handleMediaStateChanged);

    return () => {
      socket.off('user_joined', handleUserJoined);
      socket.off('webrtc_offer', handleWebRTCOffer);
      socket.off('webrtc_answer', handleWebRTCAnswer);
      socket.off('webrtc_ice_candidate', handleWebRTCCandidate);
      socket.off('user_left', handleUserLeft);
      socket.off('media_state_changed', handleMediaStateChanged);

      // Cleanup local tracks & peer connections on unmount
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      Object.values(peerConnections.current).forEach((pc) => pc.close());
      peerConnections.current = {};
      leaveRoom();
    };
  }, [socket, isConnected, roomCode, joinRoom, leaveRoom, initLocalStream]);

  // Media Controls: Audio Mute Toggle
  const toggleAudio = useCallback(() => {
    if (localStreamRef.current) {
      const audioTrack = localStreamRef.current.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        const muted = !audioTrack.enabled;
        setIsAudioMuted(muted);

        if (socket) {
          socket.emit('media_state_change', {
            room_code: roomCode,
            is_audio_muted: muted,
            is_video_off: isVideoOff,
            is_screen_sharing: isScreenSharing,
            hand_raised: handRaised,
          });
        }
      }
    }
  }, [socket, roomCode, isVideoOff, isScreenSharing, handRaised]);

  // Media Controls: Video Camera Toggle
  const toggleVideo = useCallback(() => {
    if (localStreamRef.current) {
      const videoTrack = localStreamRef.current.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        const off = !videoTrack.enabled;
        setIsVideoOff(off);

        if (socket) {
          socket.emit('media_state_change', {
            room_code: roomCode,
            is_audio_muted: isAudioMuted,
            is_video_off: off,
            is_screen_sharing: isScreenSharing,
            hand_raised: handRaised,
          });
        }
      }
    }
  }, [socket, roomCode, isAudioMuted, isScreenSharing, handRaised]);

  // Media Controls: Screen Share Toggle
  const toggleScreenShare = useCallback(async () => {
    if (isScreenSharing) {
      // Stop Screen Share -> Revert to Camera
      if (screenStreamRef.current) {
        screenStreamRef.current.getTracks().forEach((t) => t.stop());
      }
      setIsScreenSharing(false);

      if (socket) {
        socket.emit('media_state_change', {
          room_code: roomCode,
          is_audio_muted: isAudioMuted,
          is_video_off: isVideoOff,
          is_screen_sharing: false,
          hand_raised: handRaised,
        });
      }
    } else {
      // Start Screen Share
      try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
        screenStreamRef.current = screenStream;
        setIsScreenSharing(true);

        const screenTrack = screenStream.getVideoTracks()[0];

        // Replace video track across all active peer connections
        Object.values(peerConnections.current).forEach((pc) => {
          const sender = pc.getSenders().find((s) => s.track?.kind === 'video');
          if (sender) {
            sender.replaceTrack(screenTrack);
          }
        });

        screenTrack.onended = () => {
          setIsScreenSharing(false);
          if (localStreamRef.current) {
            const camTrack = localStreamRef.current.getVideoTracks()[0];
            Object.values(peerConnections.current).forEach((pc) => {
              const sender = pc.getSenders().find((s) => s.track?.kind === 'video');
              if (sender && camTrack) {
                sender.replaceTrack(camTrack);
              }
            });
          }
        };

        if (socket) {
          socket.emit('media_state_change', {
            room_code: roomCode,
            is_audio_muted: isAudioMuted,
            is_video_off: isVideoOff,
            is_screen_sharing: true,
            hand_raised: handRaised,
          });
        }
      } catch (err) {
        console.warn('Screen share cancelled or failed:', err);
      }
    }
  }, [isScreenSharing, socket, roomCode, isAudioMuted, isVideoOff, handRaised]);

  // Media Controls: Hand Raise Toggle
  const toggleHandRaise = useCallback(() => {
    const nextState = !handRaised;
    setHandRaised(nextState);

    if (socket) {
      socket.emit('media_state_change', {
        room_code: roomCode,
        is_audio_muted: isAudioMuted,
        is_video_off: isVideoOff,
        is_screen_sharing: isScreenSharing,
        hand_raised: nextState,
      });
    }
  }, [handRaised, socket, roomCode, isAudioMuted, isVideoOff, isScreenSharing]);

  // Compile combined local + remote peer list for Grid rendering
  const allStreams: PeerStream[] = [
    {
      sid: socket?.id || 'local',
      userId: user?.id,
      name: (user?.display_name || user?.username || 'You') + ' (You)',
      stream: localStream,
      isLocal: true,
      isAudioMuted,
      isVideoOff,
      isScreenSharing,
      handRaised,
    },
    ...peers,
  ];

  return {
    localStream,
    allStreams,
    isAudioMuted,
    isVideoOff,
    isScreenSharing,
    handRaised,
    mediaError,
    toggleAudio,
    toggleVideo,
    toggleScreenShare,
    toggleHandRaise,
  };
};

export default useWebRTC;
