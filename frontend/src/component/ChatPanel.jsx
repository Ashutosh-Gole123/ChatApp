import React, { useContext, useEffect, useState } from "react";
import { ChatContext } from "./context/ChatContext";
import socketService from "./services/socketServices";
import "../App.css";
import ChatHeader from "./chat_panel/ChatHeader";
import ConversationSummary from "./chat_panel/ConversationSummary";
import MessagesContainer from "./chat_panel/MessageContainer";
import SmartReplies from "./chat_panel/SmartReplies";
import MessageInput from "./chat_panel/MessageInput";
import AIToolsPanel from "./chat_panel/AIToolsPanel";

function ChatPanel() {
  // State management
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [img, setImg] = useState(null);
  const { data } = useContext(ChatContext);
  const [email, setEmail] = useState(localStorage.getItem("Email") || "");
  const [receiverId, setReceiverId] = useState(localStorage.getItem("ReceiverId") || "");
  
  // AI-related states
  const [smartReplies, setSmartReplies] = useState([]);
  const [showAITools, setShowAITools] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [conversationSummary, setConversationSummary] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("es");
  const [enhancementType, setEnhancementType] = useState("grammar");

  // Socket setup and cleanup
  useEffect(() => {
    const socket = socketService.connect();
    
    // Join room and fetch messages
    socketService.joinRoom(data.chatId);
    socketService.fetchMessages(data.chatId);

    // Set up event listeners
    setupSocketListeners();

    // Cleanup on unmount
    return () => {
      socketService.removeAllListeners();
    };
  }, [data.chatId]);

const shouldShowSmartReplies = () => {
  if (smartReplies.length === 0 || messages.length === 0) return false;
  const lastMessage = messages[messages.length - 1];
  console.log(lastMessage.receiver_id)
  // Show smart replies only if the last message was received by current user
  // Based on your backend logic: sender_id contains receiver, receiver_id contains sender
  // So current user received the message when sender_id equals current user ID
  return lastMessage.receiver_id && lastMessage.receiver_id.toString() === data.user.user_id.toString();
};
  
  const setupSocketListeners = () => {
    socketService.onMessagesReceived((response) => {
      console.log("Messages fetched:", response.messages);
      setMessages(response.messages);
    });

    socketService.onNewMessage((newMessage) => {
      console.log("New message received:", newMessage);
      console.log("Message sender_id (actually receiver):", newMessage.sender_id);
      console.log("Message receiver_id (actually sender):", newMessage.receiver_id);
      console.log("Current user_id:", data.user.user_id);
      
      setMessages((prevMessages) => [...prevMessages, newMessage]);
      
      // Auto-generate smart replies for received messages
      // Since backend swaps sender/receiver:
      // - sender_id actually contains the receiver ID
      // - receiver_id actually contains the sender ID
      // Generate smart replies when current user is the receiver (sender_id field equals current user)
      if (newMessage.sender_id && newMessage.sender_id.toString() === data.user.user_id.toString()) {
        console.log("Current user is receiver - generating smart replies");
        generateSmartReplies();
      } else {
        console.log("Current user is sender - not generating smart replies");
      }
    });

    socketService.onSmartRepliesGenerated((response) => {
      setSmartReplies(response.suggestions);
    });

    socketService.onMessageTranslated((response) => {
      setText(response.translated);
      setIsTranslating(false);
    });

    socketService.onMessageEnhanced((response) => {
      console.log("=== MESSAGE ENHANCED RESPONSE ===");
      console.log("Response received:", response);
      console.log("Original:", response.original);
      console.log("Enhanced:", response.enhanced);
      console.log("Type:", response.type);
      
      setText(response.enhanced);
      setIsEnhancing(false);
    });

    socketService.onConversationSummarized((response) => {
      setConversationSummary(response.summary);
      setShowSummary(true);
    });

    socketService.onRoomJoined((data) => {
      console.log("Joined room:", data.chat_id);
    });
  };

  // Message handling
  const handleSend = () => {
  if (!text || typeof text !== 'string' || !text.trim()) {
    console.log("No valid text to send");
    return;
  }

  const messageData = {
    chat_id: data.chatId,
    sender_id: data.user.user_id,
    sender_email: data.user.email,
    receiver_id: receiverId || localStorage.getItem("ReceiverId"),
    receiver_email: email,
    message: text.trim(),
    image: img ? {
      file_name: img.name,
      file_type: img.type,
      file_data: URL.createObjectURL(img),
    } : null,
  };

  console.log("Sending message with data:", messageData);
  socketService.sendMessage(messageData);
  setText("");
  setImg(null);
  setSmartReplies([]); // Clear smart replies when sending a message
};

  const handleSmartReplyClick = (reply) => {
    setText(reply);
    setSmartReplies([]);
  };

  // AI functions
  const generateSmartReplies = () => {
    console.log("Generating smart replies for chat:", data.chatId);
    socketService.getSmartReplies(data.chatId);
  };

  const translateMessage = () => {
    if (!text || typeof text !== 'string' || !text.trim()) {
      console.log("No valid text to translate");
      return;
    }
    setIsTranslating(true);
    socketService.translateMessage(text.trim(), selectedLanguage);
  };

  const enhanceMessage = () => {
    console.log("=== ENHANCE MESSAGE DEBUG ===");
    console.log("Text state:", text);
    console.log("Text type:", typeof text);
    console.log("Text value:", JSON.stringify(text));
    
    if (!text || typeof text !== 'string' || !text.trim()) {
      console.log("No valid text to enhance");
      return;
    }
    
    console.log("Text to enhance:", text);
    console.log("Enhancement type:", enhancementType);
    console.log("Socket connected:", socketService.isConnected);
    console.log("Socket object:", socketService.getSocket());
    
    setIsEnhancing(true);
    
    const trimmedText = text.trim();
    const enhanceData = {
      text: trimmedText,
      type: enhancementType
    };
    
    console.log("Calling socketService.enhanceMessage with:", enhanceData);
    socketService.enhanceMessage(trimmedText, enhancementType);
    console.log("enhanceMessage call completed");
  };

  const summarizeConversation = () => {
    socketService.summarizeConversation(data.chatId);
  };

  // UI handlers
  const toggleAITools = () => {
    setShowAITools(!showAITools);
  };

  const closeSummary = () => {
    setShowSummary(false);
    setConversationSummary("");
  };

  // Update receiver info when localStorage changes
  useEffect(() => {
    const handleStorageChange = () => {
      setEmail(localStorage.getItem("Email") || "");
      setReceiverId(localStorage.getItem("ReceiverId") || "");
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  return (
    <div className="chat-panel flex flex-col h-screen w-full bg-white">
      {/* Header */}
      <ChatHeader
        onToggleAITools={toggleAITools}
        onSummarizeConversation={summarizeConversation}
        showAITools={showAITools}
      />

      {/* AI Tools Panel */}
      <AIToolsPanel
        isVisible={showAITools}
        selectedLanguage={selectedLanguage}
        onLanguageChange={setSelectedLanguage}
        onTranslate={translateMessage}
        isTranslating={isTranslating}
        enhancementType={enhancementType}
        onEnhancementTypeChange={setEnhancementType}
        onEnhance={enhanceMessage}
        isEnhancing={isEnhancing}
        hasText={text.trim().length > 0}
        inputText={text}
        setInputText={setText}
      />

      {/* Conversation Summary Modal */}
      <ConversationSummary
        isVisible={showSummary}
        summary={conversationSummary}
        onClose={closeSummary}
      />

      {/* Messages Container */}
      <MessagesContainer 
        messages={messages}
        currentUserId={data.user.user_id}
        // Note: Backend swaps sender/receiver, so current user's messages have receiver_id matching currentUserId
        isCurrentUserMessage={(message) => message.receiver_id && message.receiver_id.toString() === data.user.user_id.toString()}
      />

      {/* Smart Replies */}
      <SmartReplies 
  replies={smartReplies}
  onReplyClick={handleSmartReplyClick}
  isVisible={shouldShowSmartReplies()}
/>

      {/* Message Input */}
      <MessageInput
        text={text}
        onTextChange={setText}
        onSend={handleSend}
        onGenerateSmartReplies={generateSmartReplies}
      />
    </div>
  );
}

export default ChatPanel;