import { WebSocketResponse } from '../types';

type MessageHandler = (response: WebSocketResponse) => void;

export default class SocketService {
  private static instance: SocketService;
  private socket: WebSocket | null = null;
  private messageHandlers: MessageHandler[] = [];

  private constructor() {
    this.connect();
  }

  static getInstance(): SocketService {
    if (!SocketService.instance) {
      SocketService.instance = new SocketService();
    }
    return SocketService.instance;
  }

  private connect() {
    this.socket = new WebSocket('ws://localhost:8000/ws/chat');
    // this.socket = new WebSocket('ws://ai-chat-server-1bs7.onrender.com/ws/chat');
    
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messageHandlers.forEach(handler => handler(data));
    };
  }

  sendMessage(message: string) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(message);
    }
  }

  onMessage(handler: MessageHandler) {
    this.messageHandlers.push(handler);
  }

  offMessage(handler: MessageHandler) {
    this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
  }
}