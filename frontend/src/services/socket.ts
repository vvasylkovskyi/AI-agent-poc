class SocketService {
    private socket: WebSocket;
    private static instance: SocketService;
    private messageHandlers: ((message: string) => void)[] = [];

    private constructor() {
        this.socket = new WebSocket('ws://localhost:8000/ws/chat');

        this.socket.onopen = () => {
            console.log('Connected to server');
        };

        this.socket.onclose = () => {
            console.log('Disconnected from server');
        };

        this.socket.onmessage = (event) => {
            this.messageHandlers.forEach(handler => handler(event.data));
        };
    }

    public static getInstance(): SocketService {
        if (!SocketService.instance) {
            SocketService.instance = new SocketService();
        }
        return SocketService.instance;
    }

    public sendMessage(message: string): void {
        if (this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(message);
        }
    }

    public onMessage(handler: (message: string) => void): void {
        this.messageHandlers.push(handler);
    }

    public offMessage(handler: (message: string) => void): void {
        this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    }
}

export default SocketService; 