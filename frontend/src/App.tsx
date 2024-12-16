import {
  Box,
  Button,
  Container,
  MantineProvider,
  Paper,
  Stack,
  TextInput,
  Title,
} from "@mantine/core";
import "@mantine/core/styles.css";
import React, { useEffect, useState } from "react";
import SocketService from "./services/socket";
import { Message, WebSocketResponse } from "./types";

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const socketService = SocketService.getInstance();

  useEffect(() => {
    const messageHandler = (response: WebSocketResponse) => {
      setMessages((prev) => [...prev, ...response.messages]);
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

  return (
    <MantineProvider>
      <Container size="sm" h="100vh" pt="xl" pb="xl">
        <Paper shadow="md" p="md" h="calc(100vh - 4rem)">
          <Title order={2} mb="lg">
            Welcome. Begin chatting with your AI agent.
          </Title>

          <Stack gap="md" h="calc(100% - 7rem)" style={{ overflowY: "auto" }}>
            {messages.map((msg, index) => (
              <Paper
                key={index}
                p="sm"
                withBorder
                style={{
                  backgroundColor: msg.origin === "human" ? "#f0f0f0" : "white",
                  marginLeft: msg.origin === "human" ? "auto" : "0",
                  marginRight: msg.origin === "ai" ? "auto" : "0",
                  maxWidth: "80%",
                }}
              >
                {msg.content}
              </Paper>
            ))}
          </Stack>

          <Box component="form" onSubmit={sendMessage} mt="md">
            <TextInput
              placeholder="Type a message..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              rightSectionWidth={100}
              rightSection={
                <Button type="submit" fullWidth>
                  Send
                </Button>
              }
            />
          </Box>
        </Paper>
      </Container>
    </MantineProvider>
  );
};

export default App;
