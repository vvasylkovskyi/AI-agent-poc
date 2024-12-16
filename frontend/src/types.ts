export interface Message {
    content: string;
    origin: 'human' | 'ai';
}
  
export interface WebSocketResponse {
    messages: Message[];
}