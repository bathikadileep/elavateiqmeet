/**
 * ElevateIQ — React Component Unit Test Suite (Module 7)
 * =======================================================
 * Vitest + JSDOM tests for modal components, control bar,
 * participant cards, draw tools, and interactive widgets.
 *
 * Run with:
 *   npx vitest run src/tests/components.test.tsx
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// ═══════════════════════════════════════════════════════════════════════════════
// 1. SECURITY AUDIT MODAL TESTS (6 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('SecurityAuditModal Component', () => {
  it('exports SecurityAuditModal as named and default export', async () => {
    const module = await import('../components/security/SecurityAuditModal');
    expect(module.SecurityAuditModal).toBeDefined();
    expect(module.default).toBeDefined();
  });

  it('SecurityAuditModal is a valid React functional component', async () => {
    const { SecurityAuditModal } = await import('../components/security/SecurityAuditModal');
    expect(typeof SecurityAuditModal).toBe('function');
  });

  it('SecurityAuditModalProps interface requires isOpen, onClose, isE2EEEnabled, onToggleE2EE', async () => {
    const { SecurityAuditModal } = await import('../components/security/SecurityAuditModal');
    // Component should accept required props without throwing type errors
    const props = {
      isOpen: false,
      onClose: vi.fn(),
      isE2EEEnabled: false,
      onToggleE2EE: vi.fn(),
    };
    expect(() => SecurityAuditModal(props)).not.toThrow();
  });

  it('returns null when isOpen is false', async () => {
    const { SecurityAuditModal } = await import('../components/security/SecurityAuditModal');
    const result = SecurityAuditModal({
      isOpen: false,
      onClose: vi.fn(),
      isE2EEEnabled: false,
      onToggleE2EE: vi.fn(),
    });
    expect(result).toBeNull();
  });

  it('returns JSX when isOpen is true', async () => {
    const { SecurityAuditModal } = await import('../components/security/SecurityAuditModal');
    const result = SecurityAuditModal({
      isOpen: true,
      onClose: vi.fn(),
      isE2EEEnabled: true,
      onToggleE2EE: vi.fn(),
    });
    expect(result).not.toBeNull();
    expect(result).toBeTruthy();
  });

  it('E2EE toggle callback is assignable', async () => {
    const toggleFn = vi.fn();
    const { SecurityAuditModal } = await import('../components/security/SecurityAuditModal');
    const props = {
      isOpen: false,
      onClose: vi.fn(),
      isE2EEEnabled: false,
      onToggleE2EE: toggleFn,
    };
    SecurityAuditModal(props);
    expect(toggleFn).not.toHaveBeenCalled();
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 2. DEVELOPER PORTAL MODAL TESTS (5 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('DeveloperPortalModal Component', () => {
  it('exports DeveloperPortalModal as named and default export', async () => {
    const module = await import('../components/developer/DeveloperPortalModal');
    expect(module.DeveloperPortalModal).toBeDefined();
    expect(module.default).toBeDefined();
  });

  it('DeveloperPortalModal is a valid React functional component', async () => {
    const { DeveloperPortalModal } = await import('../components/developer/DeveloperPortalModal');
    expect(typeof DeveloperPortalModal).toBe('function');
  });

  it('returns null when isOpen is false', async () => {
    const { DeveloperPortalModal } = await import('../components/developer/DeveloperPortalModal');
    const result = DeveloperPortalModal({
      isOpen: false,
      onClose: vi.fn(),
    });
    expect(result).toBeNull();
  });

  it('returns JSX when isOpen is true', async () => {
    const { DeveloperPortalModal } = await import('../components/developer/DeveloperPortalModal');
    const result = DeveloperPortalModal({
      isOpen: true,
      onClose: vi.fn(),
    });
    expect(result).not.toBeNull();
  });

  it('DeveloperPortalModalProps requires isOpen and onClose', async () => {
    const { DeveloperPortalModal } = await import('../components/developer/DeveloperPortalModal');
    const props = { isOpen: false, onClose: vi.fn() };
    expect(() => DeveloperPortalModal(props)).not.toThrow();
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 3. RECORDING PLAYER MODAL TESTS (5 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('RecordingPlayerModal Component', () => {
  it('exports RecordingPlayerModal as named and default export', async () => {
    const module = await import('../components/recordings/RecordingPlayerModal');
    expect(module.RecordingPlayerModal).toBeDefined();
    expect(module.default).toBeDefined();
  });

  it('returns null when isOpen is false', async () => {
    const { RecordingPlayerModal } = await import('../components/recordings/RecordingPlayerModal');
    const result = RecordingPlayerModal({
      isOpen: false,
      onClose: vi.fn(),
      recording: null,
    });
    expect(result).toBeNull();
  });

  it('returns null when recording is null', async () => {
    const { RecordingPlayerModal } = await import('../components/recordings/RecordingPlayerModal');
    const result = RecordingPlayerModal({
      isOpen: true,
      onClose: vi.fn(),
      recording: null,
    });
    expect(result).toBeNull();
  });

  it('returns JSX when isOpen and recording are valid', async () => {
    const { RecordingPlayerModal } = await import('../components/recordings/RecordingPlayerModal');
    const mockRecording = {
      id: 'rec-001',
      meeting_id: 'meet-001',
      status: 'available',
      duration_seconds: 120,
      download_url: '/recordings/rec-001.webm',
      hls_playlist_url: '/recordings/hls/index.m3u8',
    };
    const result = RecordingPlayerModal({
      isOpen: true,
      onClose: vi.fn(),
      recording: mockRecording as any,
    });
    expect(result).not.toBeNull();
  });

  it('RecordingPlayerModal is a function component', async () => {
    const { RecordingPlayerModal } = await import('../components/recordings/RecordingPlayerModal');
    expect(typeof RecordingPlayerModal).toBe('function');
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 4. CONTROL BAR COMPONENT TESTS (8 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('ControlBar Component', () => {
  const defaultProps = {
    isAudioMuted: false,
    isVideoOff: false,
    isScreenSharing: false,
    handRaised: false,
    chatOpen: false,
    participantCount: 3,
    onToggleAudio: vi.fn(),
    onToggleVideo: vi.fn(),
    onToggleScreenShare: vi.fn(),
    onToggleHandRaise: vi.fn(),
    onToggleChat: vi.fn(),
    onLeave: vi.fn(),
  };

  it('exports ControlBar as named export', async () => {
    const module = await import('../components/room/ControlBar');
    expect(module.ControlBar).toBeDefined();
  });

  it('ControlBar is a valid function component', async () => {
    const { ControlBar } = await import('../components/room/ControlBar');
    expect(typeof ControlBar).toBe('function');
  });

  it('renders with default props without throwing', async () => {
    const { ControlBar } = await import('../components/room/ControlBar');
    expect(() => ControlBar(defaultProps)).not.toThrow();
  });

  it('renders with audio muted state', async () => {
    const { ControlBar } = await import('../components/room/ControlBar');
    const result = ControlBar({ ...defaultProps, isAudioMuted: true });
    expect(result).toBeTruthy();
  });

  it('renders with video off state', async () => {
    const { ControlBar } = await import('../components/room/ControlBar');
    const result = ControlBar({ ...defaultProps, isVideoOff: true });
    expect(result).toBeTruthy();
  });

  it('renders with screen sharing active', async () => {
    const { ControlBar } = await import('../components/room/ControlBar');
    const result = ControlBar({ ...defaultProps, isScreenSharing: true });
    expect(result).toBeTruthy();
  });

  it('renders with hand raised', async () => {
    const { ControlBar } = await import('../components/room/ControlBar');
    const result = ControlBar({ ...defaultProps, handRaised: true });
    expect(result).toBeTruthy();
  });

  it('renders with optional props (subtitles, recording, E2EE)', async () => {
    const { ControlBar } = await import('../components/room/ControlBar');
    const result = ControlBar({
      ...defaultProps,
      subtitlesEnabled: true,
      isRecording: true,
      isE2EEEnabled: true,
      onOpenDiagnostics: vi.fn(),
      onOpenWhiteboard: vi.fn(),
      onOpenPolls: vi.fn(),
      onOpenBreakout: vi.fn(),
      onToggleSubtitles: vi.fn(),
      onToggleRecording: vi.fn(),
      onOpenSecurityAudit: vi.fn(),
      onOpenDeveloperPortal: vi.fn(),
    });
    expect(result).toBeTruthy();
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 5. POLL MODAL COMPONENT TESTS (4 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('PollModal Component', () => {
  it('exports PollModal default export', async () => {
    const module = await import('../components/polls/PollModal');
    expect(module.default).toBeDefined();
  });

  it('PollModal is a function component', async () => {
    const module = await import('../components/polls/PollModal');
    expect(typeof module.default).toBe('function');
  });

  it('PollCreateModal exports correctly', async () => {
    const module = await import('../components/polls/PollCreateModal');
    expect(module.default).toBeDefined();
  });

  it('PollCreateModal is a function component', async () => {
    const module = await import('../components/polls/PollCreateModal');
    expect(typeof module.default).toBe('function');
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 6. COMMON COMPONENT EXPORT TESTS (5 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('Common Component Exports', () => {
  it('Spinner component exports correctly', async () => {
    const module = await import('../components/common/Spinner');
    expect(module.default).toBeDefined();
  });

  it('Button component exports correctly', async () => {
    const module = await import('../components/common/Button');
    expect(module.default).toBeDefined();
  });

  it('Input component exports correctly', async () => {
    const module = await import('../components/common/Input');
    expect(module.default).toBeDefined();
  });

  it('Badge component exports correctly', async () => {
    const module = await import('../components/common/Badge');
    expect(module.default).toBeDefined();
  });

  it('TextInput component exports correctly', async () => {
    const module = await import('../components/common/TextInput');
    expect(module.default).toBeDefined();
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 7. PAGE COMPONENT EXPORT TESTS (6 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('Page Component Exports', () => {
  it('Login page exports correctly', async () => {
    const module = await import('../pages/Login');
    expect(module.Login || module.default).toBeDefined();
  });

  it('Register page exports correctly', async () => {
    const module = await import('../pages/Register');
    expect(module.default).toBeDefined();
  });

  it('Dashboard page exports correctly', async () => {
    const module = await import('../pages/Dashboard');
    expect(module.default).toBeDefined();
  });

  it('MeetingRoom page exports correctly', async () => {
    const module = await import('../pages/MeetingRoom');
    expect(module.default).toBeDefined();
  });

  it('MeetingHistory page exports correctly', async () => {
    const module = await import('../pages/MeetingHistory');
    expect(module.default).toBeDefined();
  });

  it('AdminPanel page exports correctly', async () => {
    const module = await import('../pages/AdminPanel');
    expect(module.default).toBeDefined();
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 8. CHAT DRAWER COMPONENT TESTS (3 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('ChatDrawer Component', () => {
  it('ChatDrawer exports correctly', async () => {
    const module = await import('../components/chat/ChatDrawer');
    expect(module.default).toBeDefined();
  });

  it('ChatDrawer is a function component', async () => {
    const module = await import('../components/chat/ChatDrawer');
    expect(typeof module.default).toBe('function');
  });

  it('NotificationDrawer exports correctly', async () => {
    const module = await import('../components/notifications/NotificationDrawer');
    expect(module.default).toBeDefined();
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 9. WHITEBOARD COMPONENT TESTS (3 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('Whiteboard Components', () => {
  it('WhiteboardModal exports correctly', async () => {
    const module = await import('../components/whiteboard/WhiteboardModal');
    expect(module.default).toBeDefined();
  });

  it('Canvas component exports correctly', async () => {
    const module = await import('../components/whiteboard/Canvas');
    expect(module.default).toBeDefined();
  });

  it('WhiteboardModal is a function component', async () => {
    const module = await import('../components/whiteboard/WhiteboardModal');
    expect(typeof module.default).toBe('function');
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 10. AISummaryModal TESTS (3 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('AISummaryModal Component', () => {
  it('AISummaryModal exports correctly', async () => {
    const module = await import('../components/room/AISummaryModal');
    expect(module.default).toBeDefined();
  });

  it('AISummaryModal is a function component', async () => {
    const module = await import('../components/room/AISummaryModal');
    expect(typeof module.default).toBe('function');
  });

  it('CaptionOverlay exports correctly', async () => {
    const module = await import('../components/room/CaptionOverlay');
    expect(module.default).toBeDefined();
  });
});
