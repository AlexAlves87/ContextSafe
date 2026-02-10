/**
 * WebSocket Service - Real-time Updates
 *
 * Traceability:
 * - Binding Contract: UI-BIND-003 (ProcessingProgress)
 * - project_context.yaml#presentation.web.realtime_client: websocket-native
 */

import type { ProcessingProgress, ProcessingStage } from '@/types';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface ProgressMessage {
  type: 'progress';
  documentId: string;
  stage: ProcessingStage;
  progress: number;
  currentEntity?: string;
}

export interface CompleteMessage {
  type: 'complete';
  documentId: string;
}

export interface ErrorMessage {
  type: 'error';
  documentId: string;
  message: string;
}

export type WebSocketMessage = ProgressMessage | CompleteMessage | ErrorMessage;

export type ProgressCallback = (progress: ProcessingProgress) => void;
export type CompleteCallback = (documentId: string) => void;
export type ErrorCallback = (documentId: string, error: string) => void;
export type StatusCallback = (status: WebSocketStatus) => void;

/**
 * WebSocket client for document processing progress
 */
export class ProcessingWebSocket {
  private ws: WebSocket | null = null;
  private documentId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  private onProgress: ProgressCallback | null = null;
  private onComplete: CompleteCallback | null = null;
  private onError: ErrorCallback | null = null;
  private onStatusChange: StatusCallback | null = null;

  constructor(documentId: string) {
    this.documentId = documentId;
  }

  /**
   * Connect to WebSocket server
   * Returns a promise that resolves when connected
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.updateStatus('connecting');

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const url = `${protocol}//${host}/ws/documents/${this.documentId}/progress`;

      console.log(`[WS] Connecting to ${url}`);
      this.ws = new WebSocket(url);

      // Timeout after 5 seconds
      const timeout = setTimeout(() => {
        console.error('[WS] Connection timeout');
        reject(new Error('WebSocket connection timeout'));
      }, 5000);

      this.ws.onopen = () => {
        clearTimeout(timeout);
        this.reconnectAttempts = 0;
        this.updateStatus('connected');
        console.log('[WS] Connected successfully');
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('[WS] Message received:', message);
          this.handleMessage(message);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.ws.onerror = (error) => {
        clearTimeout(timeout);
        console.error('[WS] Error:', error);
        this.updateStatus('error');
        reject(new Error('WebSocket connection error'));
      };

      this.ws.onclose = () => {
        this.updateStatus('disconnected');
        this.attemptReconnect();
      };
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
  }

  /**
   * Set progress callback
   */
  setOnProgress(callback: ProgressCallback): void {
    this.onProgress = callback;
  }

  /**
   * Set complete callback
   */
  setOnComplete(callback: CompleteCallback): void {
    this.onComplete = callback;
  }

  /**
   * Set error callback
   */
  setOnError(callback: ErrorCallback): void {
    this.onError = callback;
  }

  /**
   * Set status change callback
   */
  setOnStatusChange(callback: StatusCallback): void {
    this.onStatusChange = callback;
  }

  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'progress':
        this.onProgress?.({
          documentId: message.documentId,
          stage: message.stage,
          progress: message.progress,
          currentEntity: message.currentEntity,
        });
        break;

      case 'complete':
        this.onComplete?.(message.documentId);
        this.disconnect();
        break;

      case 'error':
        this.onError?.(message.documentId, message.message);
        break;
    }
  }

  private updateStatus(status: WebSocketStatus): void {
    this.onStatusChange?.(status);
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    setTimeout(() => {
      this.connect();
    }, delay);
  }
}

/**
 * Factory function to create WebSocket connection
 */
export function createProgressWebSocket(documentId: string): ProcessingWebSocket {
  return new ProcessingWebSocket(documentId);
}
