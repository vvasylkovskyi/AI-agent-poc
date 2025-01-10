export interface Message {
    user: string;
    msg: string
    origin: 'human' | 'ai';
}
  
export interface WebSocketResponse {
    messages: Message[];
}