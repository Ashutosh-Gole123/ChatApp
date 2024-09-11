import React, { useState, useContext, useEffect } from "react";
import io from "socket.io-client";
import { ChatContext } from "./context/ChatContext";

// Initialize your Socket.IO client connection
const socket = io("http://localhost:5000");

const InputField = () => {
  const [text, setText] = useState("");
  const [img, setImg] = useState(null);
  const { data } = useContext(ChatContext); // Access the context
  const [email,setEmail] = useState('')
  useEffect(() => {
    const storedEmail = localStorage.getItem('Email');
    if (storedEmail) {
      setEmail(storedEmail);
    }
  },[])
  const handleSend = () => {
    const messageData = {
      chat_id: data.chatId,
      sender_email: data.user.email, // Assuming user object contains the sender's ID
      receiver_email: email,
      message: text,
      // Include image if it's available
      image: img ? {
        file_name: img.name,
        file_type: img.type,
        file_data: URL.createObjectURL(img) // Or handle image differently
      } : null
    };

    // Emit the message event
    socket.emit("send_message", messageData);
    // window.location.reload();

    // Reset form fields
    setText("");
    setImg(null);
  };

  return (
    <div>
      {/* Your input fields and send button here */}
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <input type="file" onChange={(e) => setImg(e.target.files[0])} />
      <button onClick={handleSend}>Send</button>
    </div>
  );
};

export default InputField;
