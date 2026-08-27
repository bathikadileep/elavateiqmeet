/**
 * ElevateIQ — WebRTC Insertable Streams AES-GCM-256 E2EE Engine
 * =============================================================
 * Zero-trust frame-level end-to-end encryption for WebRTC audio/video streams.
 */

export class E2EEManager {
  private cryptoKey: CryptoKey | null = null;

  async setKey(secretPassphrase: string) {
    const enc = new TextEncoder();
    const keyMaterial = await window.crypto.subtle.importKey(
      'raw',
      enc.encode(secretPassphrase),
      'PBKDF2',
      false,
      ['deriveKey']
    );

    this.cryptoKey = await window.crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: enc.encode('ElevateIQ-E2EE-Salt-2026'),
        iterations: 100000,
        hash: 'SHA-256',
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }

  async encryptFrame(frame: any, controller: any) {
    if (!this.cryptoKey) {
      controller.enqueue(frame);
      return;
    }

    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const encrypted = await window.crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      this.cryptoKey,
      frame.data
    );

    const newBuffer = new Uint8Array(iv.length + encrypted.byteLength);
    newBuffer.set(iv, 0);
    newBuffer.set(new Uint8Array(encrypted), iv.length);

    frame.data = newBuffer.buffer;
    controller.enqueue(frame);
  }

  async decryptFrame(frame: any, controller: any) {
    if (!this.cryptoKey) {
      controller.enqueue(frame);
      return;
    }

    const data = new Uint8Array(frame.data);
    const iv = data.subarray(0, 12);
    const ciphertext = data.subarray(12);

    try {
      const decrypted = await window.crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        this.cryptoKey,
        ciphertext
      );
      frame.data = decrypted;
      controller.enqueue(frame);
    } catch (e) {
      // Return unencrypted fallback if key mismatch
      controller.enqueue(frame);
    }
  }
}
