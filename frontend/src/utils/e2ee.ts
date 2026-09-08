/**
 * ElevateIQ — WebRTC End-to-End Encryption (E2EE) & Insertable Streams
 * ====================================================================
 * Utilizes WebCrypto AES-GCM 128/256 and WebRTC TransformStream API to encrypt
 * raw audio/video frames before WebRTC peer transport transmission.
 */

export interface E2EETransformOptions {
  sharedKey: string;
  enableVideoEncryption?: boolean;
  enableAudioEncryption?: boolean;
}

export class WebRTCE2EEEngine {
  private cryptoKey: CryptoKey | null = null;
  private keyVersion: number = 1;

  public async initializeKey(secretPassphrase: string): Promise<void> {
    const encoder = new TextEncoder();
    const keyData = encoder.encode(secretPassphrase);
    const keyHash = await window.crypto.subtle.digest('SHA-256', keyData);

    this.cryptoKey = await window.crypto.subtle.importKey(
      'raw',
      keyHash,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }

  public createSenderTransform(): TransformStream {
    return new TransformStream({
      transform: async (frame: any, controller: TransformStreamDefaultController) => {
        if (!this.cryptoKey) {
          controller.enqueue(frame);
          return;
        }

        try {
          const iv = window.crypto.getRandomValues(new Uint8Array(12));
          const dataBuffer = new Uint8Array(frame.data);

          const encryptedBuffer = await window.crypto.subtle.encrypt(
            { name: 'AES-GCM', iv },
            this.cryptoKey,
            dataBuffer
          );

          const payload = new Uint8Array(12 + encryptedBuffer.byteLength);
          payload.set(iv, 0);
          payload.set(new Uint8Array(encryptedBuffer), 12);

          frame.data = payload.buffer;
          controller.enqueue(frame);
        } catch (err) {
          console.warn('E2EE encryption frame transform error:', err);
          controller.enqueue(frame);
        }
      },
    });
  }

  public createReceiverTransform(): TransformStream {
    return new TransformStream({
      transform: async (frame: any, controller: TransformStreamDefaultController) => {
        if (!this.cryptoKey) {
          controller.enqueue(frame);
          return;
        }

        try {
          const dataBuffer = new Uint8Array(frame.data);
          if (dataBuffer.byteLength < 13) {
            controller.enqueue(frame);
            return;
          }

          const iv = dataBuffer.subarray(0, 12);
          const encryptedData = dataBuffer.subarray(12);

          const decryptedBuffer = await window.crypto.subtle.decrypt(
            { name: 'AES-GCM', iv },
            this.cryptoKey,
            encryptedData
          );

          frame.data = decryptedBuffer;
          controller.enqueue(frame);
        } catch (err) {
          console.warn('E2EE decryption frame transform error:', err);
          controller.enqueue(frame);
        }
      },
    });
  }
}

export class E2EEManager {
  private engine: WebRTCE2EEEngine = new WebRTCE2EEEngine();
  private currentKey: string = '';

  public async setKey(passphrase: string): Promise<void> {
    this.currentKey = passphrase;
    await this.engine.initializeKey(passphrase);
  }

  public getKey(): string {
    return this.currentKey;
  }

  public getEngine(): WebRTCE2EEEngine {
    return this.engine;
  }
}
