import { useState, useEffect, useRef, useCallback } from 'react';
import type { Socket } from 'socket.io-client';
import type { WhiteboardTool, WhiteboardStroke } from '../types/collaboration';

export interface UseWhiteboardOptions {
  socket: Socket | null;
  roomCode: string;
}

export const useWhiteboard = ({ socket, roomCode }: UseWhiteboardOptions) => {
  const [strokes, setStrokes] = useState<WhiteboardStroke[]>([]);
  const [undoStack, setUndoStack] = useState<WhiteboardStroke[][]>([]);
  const [activeTool, setActiveTool] = useState<WhiteboardTool>('pencil');
  const [activeColor, setActiveColor] = useState<string>('#6366f1');
  const [strokeWidth, setStrokeWidth] = useState<number>(3);
  const [laserPoint, setLaserPoint] = useState<{ x: number; y: number } | null>(null);

  // Fetch initial whiteboard canvas snapshot from database via Socket.IO
  useEffect(() => {
    if (!socket || !roomCode) return;

    socket.emit('whiteboard_get_state', { room_code: roomCode });

    const handleStateResponse = (data: { snapshot_json: WhiteboardStroke[] }) => {
      if (Array.isArray(data.snapshot_json)) {
        setStrokes(data.snapshot_json);
      }
    };

    const handleRemoteDraw = (data: { stroke: WhiteboardStroke }) => {
      if (data.stroke) {
        setStrokes((prev) => [...prev, data.stroke]);
      }
    };

    const handleRemoteClear = () => {
      setStrokes([]);
    };

    socket.on('whiteboard_state_response', handleStateResponse);
    socket.on('whiteboard_draw_event', handleRemoteDraw);
    socket.on('whiteboard_cleared', handleRemoteClear);

    return () => {
      socket.off('whiteboard_state_response', handleStateResponse);
      socket.off('whiteboard_draw_event', handleRemoteDraw);
      socket.off('whiteboard_cleared', handleRemoteClear);
    };
  }, [socket, roomCode]);

  const addStroke = useCallback(
    (stroke: WhiteboardStroke) => {
      setUndoStack((prev) => [...prev, strokes]);
      setStrokes((prev) => {
        const next = [...prev, stroke];
        if (socket) {
          socket.emit('whiteboard_draw_event', { room_code: roomCode, stroke });
          socket.emit('whiteboard_save_state', { room_code: roomCode, snapshot_json: next });
        }
        return next;
      });
    },
    [strokes, socket, roomCode]
  );

  const clearCanvas = useCallback(() => {
    setUndoStack((prev) => [...prev, strokes]);
    setStrokes([]);
    if (socket) {
      socket.emit('whiteboard_clear', { room_code: roomCode });
      socket.emit('whiteboard_save_state', { room_code: roomCode, snapshot_json: [] });
    }
  }, [strokes, socket, roomCode]);

  const undo = useCallback(() => {
    if (undoStack.length === 0) return;
    const previous = undoStack[undoStack.length - 1];
    setUndoStack((prev) => prev.slice(0, prev.length - 1));
    setStrokes(previous);
    if (socket) {
      socket.emit('whiteboard_save_state', { room_code: roomCode, snapshot_json: previous });
    }
  }, [undoStack, socket, roomCode]);

  return {
    strokes,
    activeTool,
    activeColor,
    strokeWidth,
    laserPoint,
    setActiveTool,
    setActiveColor,
    setStrokeWidth,
    setLaserPoint,
    addStroke,
    clearCanvas,
    undo,
    canUndo: undoStack.length > 0,
  };
};
