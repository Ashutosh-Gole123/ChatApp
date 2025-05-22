import React, { useContext, useEffect, useRef, useState } from "react";
import io from "socket.io-client";
import { ChatContext } from "./context/ChatContext";
import InputField from "./InputField";
import "../App.css";
// Initialize your Socket.IO client connection
const socket = io("http://localhost:5000", {
  transports: ["websocket"], // For WebSocket connection
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  debug: true, // Enable debugging
});
function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [img, setImg] = useState(null);
  const { data } = useContext(ChatContext); // Access the context
  const [email, setEmail] = useState(localStorage.getItem("Email") || "");
  const chatPanelRef = useRef(null);
  useEffect(() => {
    // Fetch messages and listen for new messages when component mounts
    socket.on("connect", () => {
      console.log("Connected to server");

      // Join the chat room
      
      // Fetch existing messages
    });
    socket.emit("join_room", { chat_id: data.chatId });
    socket.emit("fetch_messages", { chat_id: data.chatId });

    socket.on("messages_fetched", (response) => {
      console.log("Messages fetched:", response.messages);
      setMessages(response.messages);
    });

    socket.on("new_message", (newMessage) => {
      console.log("New message received:", newMessage.message);
      setMessages((prevMessages) => [...prevMessages, newMessage]);
    });
    socket.emit("send_message",  {chat_id: data.chatId,
      sender_email: email,
      receiver_email: data.receiverEmail,
      message: text});

    socket.on("room_joined", (data) => {
      console.log("Joined room:", data.chat_id);
    });

    // Clean up socket listeners on component unmount
    return () => {
      console.log("Cleaning up socket listeners");
      socket.off("connect");
      socket.off("messages_fetched");
      socket.off("new_message");
      socket.off("room_joined");
    };
  }, [data.chatId]);
  useEffect(() => {
    if (chatPanelRef.current) {
      chatPanelRef.current.scrollTop = chatPanelRef.current.scrollHeight;
    }
  }, [messages]);
  const handleSend = () => {
    const messageData = {
      chat_id: data.chatId,
      sender_email: data.user.email, // Assuming user object contains the sender's ID
      receiver_email: email,
      message: text,
      // Include image if it's available
      image: img
        ? {
            file_name: img.name,
            file_type: img.type,
            file_data: URL.createObjectURL(img), // Or handle image differently
          }
        : null,
    };

    // Emit the message event
    socket.emit("send_message", messageData);

    // Reset form fields
    setText("");
    setImg(null);
  };

  return (
    <div className="chat-panel flex flex-col h-screen w-full bg-zinc-600">
  {/* Messages container */}
  <div className="messages-container flex-1 overflow-y-auto p-3" ref={chatPanelRef}>
    {messages.map((msg) => (
      <div
        key={msg.message_id}
        className={`flex ${msg.sender_id === data.user.user_id ? "justify-end" : "justify-start"} mb-2`}
      >
        <div
          className={`p-3 rounded-lg ${msg.sender_id === data.user.user_id ? "bg-blue-500 text-white" : "bg-gray-300 text-black"}`}
        >
          <p>{msg.message}</p>
          <span className="block text-xs text-gray-600">{new Date(msg.timestamp).toLocaleString()}</span>
        </div>
      </div>
    ))}
  </div>
  
  {/* Input container */}
  <div className="input-container flex p-3 bg-gray-800 sticky bottom-0 w-full">
    <input
      type="text"
      value={text}
      onChange={(e) => setText(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          handleSend();
        }
      }}
      className="flex-1 p-2 border border-gray-300 rounded"
      placeholder="Type a message"
    />
    <button
      onClick={handleSend}
      className="ml-2 bg-blue-500 text-white p-2 rounded"
    >
      Send
    </button>
  </div>
</div>

  );
}

export default ChatPanel;
