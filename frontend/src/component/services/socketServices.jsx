import io from "socket.io-client";

class SocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
  }

  connect(url = "http://localhost:5000") {
    if (this.socket && this.isConnected) {
      return this.socket;
    }

    this.socket = io(url, {
      transports: ["websocket"],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      debug: true,
    });

    this.socket.on("connect", () => {
      console.log("Connected to server");
      this.isConnected = true;
    });

    this.socket.on("disconnect", () => {
      console.log("Disconnected from server");
      this.isConnected = false;
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
    }
  }

  // Chat Methods
  joinRoom(chatId) {
    if (this.socket) {
      this.socket.emit("join_room", { chat_id: chatId });
    }
  }

  fetchMessages(chatId) {
    if (this.socket) {
      this.socket.emit("fetch_messages", { chat_id: chatId });
    }
  }

  sendMessage(messageData) {
    if (this.socket) {
      this.socket.emit("send_message", messageData);
    }
  }

  // AI Methods
  getSmartReplies(chatId) {
    if (this.socket) {
      this.socket.emit("get_smart_replies", { chat_id: chatId });
    }
  }

  translateMessage(text, targetLanguage, callback) {
  if (this.socket) {
    this.socket.emit("translate_message", {
      text: text,
      target_language: targetLanguage
    });

    this.socket.once("message_translated", (data) => {
      callback(null, data);
    });

    this.socket.once("error", (err) => {
      callback(err, null);
    });
  }
}



  enhanceMessage(text, enhancementType) {
  return new Promise((resolve, reject) => {
    if (this.socket) {
      this.socket.emit("enhance_message", {
        text: text,
        type: enhancementType
      });

      this.socket.once("message_enhanced", (data) => {
        resolve(data);
      });

      this.socket.once("error", (err) => {
        reject(err);
      });
    } else {
      reject(new Error("Socket not connected"));
    }
  });
}


  summarizeConversation(chatId) {
    if (this.socket) {
      this.socket.emit("summarize_conversation", { chat_id: chatId });
    }
  }

  // Event Listeners
  onMessagesReceived(callback) {
    if (this.socket) {
      this.socket.on("messages_fetched", callback);
    }
  }

  onNewMessage(callback) {
    if (this.socket) {
      this.socket.on("new_message", callback);
    }
  }

  onSmartRepliesGenerated(callback) {
    if (this.socket) {
      this.socket.on("smart_replies_generated", callback);
    }
  }

  onMessageTranslated(callback) {
    if (this.socket) {
      this.socket.on("message_translated", callback);
    }
  }

  onMessageEnhanced(callback) {
    if (this.socket) {
      this.socket.on("message_enhanced", callback);
    }
  }

  onConversationSummarized(callback) {
    if (this.socket) {
      this.socket.on("conversation_summarized", callback);
    }
  }

  onRoomJoined(callback) {
    if (this.socket) {
      this.socket.on("room_joined", callback);
    }
  }

  // Remove event listeners
  removeAllListeners() {
    if (this.socket) {
      this.socket.off("messages_fetched");
      this.socket.off("new_message");
      this.socket.off("smart_replies_generated");
      this.socket.off("message_translated");
      this.socket.off("message_enhanced");
      this.socket.off("conversation_summarized");
      this.socket.off("room_joined");
    }
  }

  getSocket() {
    return this.socket;
  }
}

// Create singleton instance
const socketService = new SocketService();
export default socketService;