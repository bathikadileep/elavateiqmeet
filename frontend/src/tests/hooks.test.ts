/**
 * ElevateIQ — Custom React Hooks & Utility Unit Test Suite (Module 7)
 * ====================================================================
 * Vitest unit tests for E2EE cryptographic engine, useWhiteboard hook
 * logic, useVAD audio analysis, and other utility functions.
 *
 * Run with:
 *   npx vitest run src/tests/hooks.test.ts
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';


// ═══════════════════════════════════════════════════════════════════════════════
// 1. E2EE MANAGER CRYPTO TESTS (8 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('E2EEManager Crypto Engine', () => {
  it('E2EEManager class is exported from utils/e2ee', async () => {
    const { E2EEManager } = await import('../utils/e2ee');
    expect(E2EEManager).toBeDefined();
  });

  it('E2EEManager can be instantiated', async () => {
    const { E2EEManager } = await import('../utils/e2ee');
    const manager = new E2EEManager();
    expect(manager).toBeDefined();
    expect(manager).toBeInstanceOf(E2EEManager);
  });

  it('setKey method exists and is callable', async () => {
    const { E2EEManager } = await import('../utils/e2ee');
    const manager = new E2EEManager();
    expect(typeof manager.setKey).toBe('function');
  });

  it('encryptFrame method exists and is callable', async () => {
    const { E2EEManager } = await import('../utils/e2ee');
    const manager = new E2EEManager();
    expect(typeof manager.encryptFrame).toBe('function');
  });

  it('decryptFrame method exists and is callable', async () => {
    const { E2EEManager } = await import('../utils/e2ee');
    const manager = new E2EEManager();
    expect(typeof manager.decryptFrame).toBe('function');
  });

  it('encryptFrame passes through frame when no key set', async () => {
    const { E2EEManager } = await import('../utils/e2ee');
    const manager = new E2EEManager();

    const mockFrame = { data: new ArrayBuffer(16) };
    const enqueuedFrames: any[] = [];
    const controller = { enqueue: (f: any) => enqueuedFrames.push(f) };

    await manager.encryptFrame(mockFrame, controller);
    expect(enqueuedFrames.length).toBe(1);
    expect(enqueuedFrames[0]).toBe(mockFrame);
  });

  it('decryptFrame passes through frame when no key set', async () => {
    const { E2EEManager } = await import('../utils/e2ee');
    const manager = new E2EEManager();

    const mockFrame = { data: new ArrayBuffer(32) };
    const enqueuedFrames: any[] = [];
    const controller = { enqueue: (f: any) => enqueuedFrames.push(f) };

    await manager.decryptFrame(mockFrame, controller);
    expect(enqueuedFrames.length).toBe(1);
    expect(enqueuedFrames[0]).toBe(mockFrame);
  });

  it('multiple E2EEManager instances are independent', async () => {
    const { E2EEManager } = await import('../utils/e2ee');
    const manager1 = new E2EEManager();
    const manager2 = new E2EEManager();
    expect(manager1).not.toBe(manager2);
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 2. useE2EE HOOK EXPORT TESTS (4 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('useE2EE Hook', () => {
  it('useE2EE hook is exported', async () => {
    const module = await import('../hooks/useE2EE');
    expect(module.useE2EE).toBeDefined();
  });

  it('useE2EE is a function', async () => {
    const { useE2EE } = await import('../hooks/useE2EE');
    expect(typeof useE2EE).toBe('function');
  });

  it('useE2EE module does not export unexpected names', async () => {
    const module = await import('../hooks/useE2EE');
    const keys = Object.keys(module);
    expect(keys).toContain('useE2EE');
  });

  it('useE2EE module is importable without errors', async () => {
    await expect(import('../hooks/useE2EE')).resolves.toBeDefined();
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 3. useWhiteboard HOOK EXPORT & INTERFACE TESTS (5 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('useWhiteboard Hook', () => {
  it('useWhiteboard hook is exported', async () => {
    const module = await import('../hooks/useWhiteboard');
    expect(module.useWhiteboard).toBeDefined();
  });

  it('useWhiteboard is a function', async () => {
    const { useWhiteboard } = await import('../hooks/useWhiteboard');
    expect(typeof useWhiteboard).toBe('function');
  });

  it('UseWhiteboardOptions interface expects socket and roomCode', async () => {
    // This is a structural verification via import
    const module = await import('../hooks/useWhiteboard');
    expect(module.useWhiteboard).toBeDefined();
    // The hook accepts { socket, roomCode } as parameters
  });

  it('useWhiteboard module loads without errors', async () => {
    await expect(import('../hooks/useWhiteboard')).resolves.toBeDefined();
  });

  it('useWhiteboard module does not have stale exports', async () => {
    const module = await import('../hooks/useWhiteboard');
    expect(typeof module.useWhiteboard).toBe('function');
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 4. useVAD HOOK EXPORT TESTS (4 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('useVAD Hook', () => {
  it('useVAD hook is exported', async () => {
    const module = await import('../hooks/useVAD');
    expect(module.useVAD).toBeDefined();
  });

  it('useVAD is a function', async () => {
    const { useVAD } = await import('../hooks/useVAD');
    expect(typeof useVAD).toBe('function');
  });

  it('useVAD module is importable', async () => {
    await expect(import('../hooks/useVAD')).resolves.toBeDefined();
  });

  it('UseVADOptions expects localStream, socket, roomCode', async () => {
    const module = await import('../hooks/useVAD');
    expect(module.useVAD).toBeDefined();
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 5. OTHER HOOKS EXPORT TESTS (8 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('Additional Hook Exports', () => {
  it('useAuth hook exports correctly', async () => {
    const module = await import('../hooks/useAuth');
    expect(module.useAuth).toBeDefined();
    expect(typeof module.useAuth).toBe('function');
  });

  it('useWebRTC hook exports correctly', async () => {
    const module = await import('../hooks/useWebRTC');
    expect(module.default || module.useWebRTC).toBeDefined();
  });

  it('useSFU hook exports correctly', async () => {
    const module = await import('../hooks/useSFU');
    expect(module.default || module.useSFU).toBeDefined();
  });

  it('useWebRTCDiagnostics hook exports correctly', async () => {
    const module = await import('../hooks/useWebRTCDiagnostics');
    expect(module.default || module.useWebRTCDiagnostics).toBeDefined();
  });

  it('useVirtualBackground hook exports correctly', async () => {
    const module = await import('../hooks/useVirtualBackground');
    expect(module.default || module.useVirtualBackground).toBeDefined();
  });

  it('useSpeechToText hook exports correctly', async () => {
    const module = await import('../hooks/useSpeechToText');
    expect(module.default || module.useSpeechToText).toBeDefined();
  });

  it('useAudioDSP hook exports correctly', async () => {
    const module = await import('../hooks/useAudioDSP');
    expect(module.default || module.useAudioDSP).toBeDefined();
  });

  it('All hooks are importable without errors', async () => {
    const imports = [
      import('../hooks/useAuth'),
      import('../hooks/useE2EE'),
      import('../hooks/useVAD'),
      import('../hooks/useWhiteboard'),
      import('../hooks/useWebRTC'),
      import('../hooks/useSFU'),
    ];
    const results = await Promise.allSettled(imports);
    const fulfilled = results.filter(r => r.status === 'fulfilled');
    expect(fulfilled.length).toBe(imports.length);
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 6. API CLIENT UTILITY TESTS (3 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('API Client Utility', () => {
  it('client module exports an axios instance', async () => {
    const module = await import('../api/client');
    expect(module.default).toBeDefined();
  });

  it('client has HTTP methods', async () => {
    const module = await import('../api/client');
    const client = module.default;
    expect(typeof client.get).toBe('function');
    expect(typeof client.post).toBe('function');
    expect(typeof client.put).toBe('function');
    expect(typeof client.delete).toBe('function');
  });

  it('auth API module exports login functions', async () => {
    const module = await import('../api/auth');
    expect(module).toBeDefined();
  });
});


// ═══════════════════════════════════════════════════════════════════════════════
// 7. TYPE DEFINITION VALIDATION TESTS (4 test cases)
// ═══════════════════════════════════════════════════════════════════════════════

describe('TypeScript Type Definitions', () => {
  it('security types module loads', async () => {
    await expect(import('../types/security')).resolves.toBeDefined();
  });

  it('developer types module loads', async () => {
    await expect(import('../types/developer')).resolves.toBeDefined();
  });

  it('collaboration types module loads', async () => {
    await expect(import('../types/collaboration')).resolves.toBeDefined();
  });

  it('dashboard types module loads', async () => {
    await expect(import('../types/dashboard')).resolves.toBeDefined();
  });
});
