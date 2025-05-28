import React, { useEffect, useRef } from 'react';
import Message from './Message';

const MessagesContainer = ({ messages, currentUserId }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="messages-container flex-1 overflow-y-auto p-3">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-gray-400">
          <p>No messages yet. Start the conversation!</p>
        </div>
      ) : (
        messages.map((message) => (
          <Message 
            key={message.message_id} 
            message={message} 
            currentUserId={currentUserId} 
          />
        ))
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessagesContainer;