import React, { useEffect, useState } from "react";
import SocketService from "./services/socket";

const App: React.FC = () => {
  const [messages, setMessages] = useState<string[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const socketService = SocketService.getInstance();

  useEffect(() => {
    const messageHandler = (message: string) => {
      setMessages((prev) => [...prev, message]);
    };

    socketService.onMessage(messageHandler);

    return () => {
      socketService.offMessage(messageHandler);
    };
  }, []);

  const sendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim()) {
      socketService.sendMessage(inputMessage);
      setInputMessage("");
    }
  };

  console.log(messages);
  return (
    <div>
      <h1>AI Chat App</h1>
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index}>{msg}</div>
        ))}
      </div>
      <form onSubmit={sendMessage}>
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Type a message..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};

export default App;
