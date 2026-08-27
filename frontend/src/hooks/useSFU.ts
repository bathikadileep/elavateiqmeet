import { useEffect, useState, useRef, useCallback } from 'react';
import type { Socket } from 'socket.io-client';
import type { SFUTransportOptions, SFUProducer, SFUConsumer } from '../types/sfu';

export interface UseSFUOptions {
  socket: Socket | null;
  isConnected: boolean;
  roomCode: string;
  localStream: MediaStream | null;
}

export const useSFU = ({ socket, isConnected, roomCode, localStream }: UseSFUOptions) => {
  const [sfuActive, setSfuActive] = useState<boolean>(false);
  const [transportOptions, setTransportOptions] = useState<SFUTransportOptions | null>(null);
  const [producers, setProducers] = useState<SFUProducer[]>([]);
  const [consumers, setConsumers] = useState<SFUConsumer[]>([]);
  const [routerCapabilities, setRouterCapabilities] = useState<unknown | null>(null);

  // Request SFU Router Capabilities & Allocate Transport
  const initSFU = useCallback(() => {
    if (!socket || !isConnected || !roomCode) return;

    socket.emit('sfu_get_router_capabilities', { room_code: roomCode });
    socket.emit('sfu_create_transport', { room_code: roomCode, direction: 'sendrecv' });
  }, [socket, isConnected, roomCode]);

  useEffect(() => {
    if (!socket || !isConnected || !roomCode) return;

    initSFU();

    const handleRouterCapabilities = (data: unknown) => {
      setRouterCapabilities(data);
      setSfuActive(true);
    };

    const handleTransportCreated = (data: SFUTransportOptions) => {
      setTransportOptions(data);
      socket.emit('sfu_connect_transport', {
        room_code: roomCode,
        transport_id: data.id,
        dtlsParameters: data.dtlsParameters,
      });
    };

    const handleTransportConnected = () => {
      // If local stream exists, publish audio & video producers to SFU
      if (localStream && transportOptions) {
        localStream.getTracks().forEach((track) => {
          socket.emit('sfu_produce', {
            room_code: roomCode,
            transport_id: transportOptions.id,
            kind: track.kind,
          });
        });
      }
    };

    const handleProduced = (data: { producer_id: string; kind: 'audio' | 'video' }) => {
      setProducers((prev) => [...prev, { id: data.producer_id, kind: data.kind, paused: false }]);
    };

    const handleNewProducer = (data: { producer_id: string; producer_sid: string; kind: 'audio' | 'video' }) => {
      if (transportOptions) {
        socket.emit('sfu_consume', {
          room_code: roomCode,
          producer_id: data.producer_id,
          transport_id: transportOptions.id,
        });
      }
    };

    const handleConsumed = (data: { id: string; producer_id: string; kind: 'audio' | 'video'; current_spatial_layer: number }) => {
      setConsumers((prev) => [
        ...prev,
        {
          id: data.id,
          producerId: data.producer_id,
          kind: data.kind,
          paused: false,
          spatialLayer: data.current_spatial_layer,
        },
      ]);
    };

    socket.on('sfu_router_capabilities', handleRouterCapabilities);
    socket.on('sfu_transport_created', handleTransportCreated);
    socket.on('sfu_transport_connected', handleTransportConnected);
    socket.on('sfu_produced', handleProduced);
    socket.on('sfu_new_producer', handleNewProducer);
    socket.on('sfu_consumed', handleConsumed);

    return () => {
      socket.off('sfu_router_capabilities', handleRouterCapabilities);
      socket.off('sfu_transport_created', handleTransportCreated);
      socket.off('sfu_transport_connected', handleTransportConnected);
      socket.off('sfu_produced', handleProduced);
      socket.off('sfu_new_producer', handleNewProducer);
      socket.off('sfu_consumed', handleConsumed);
    };
  }, [socket, isConnected, roomCode, initSFU, localStream, transportOptions]);

  const setPreferredLayer = useCallback(
    (consumerId: string, spatialLayer: number) => {
      if (socket) {
        socket.emit('sfu_set_preferred_layers', {
          room_code: roomCode,
          consumer_id: consumerId,
          spatial_layer: spatialLayer,
        });
      }
    },
    [socket, roomCode]
  );

  return {
    sfuActive,
    transportOptions,
    producers,
    consumers,
    routerCapabilities,
    setPreferredLayer,
  };
};
