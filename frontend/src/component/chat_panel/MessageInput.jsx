import React from 'react';
import { Send, Sparkles } from 'lucide-react';

const MessageInput = ({ 
  text, 
  onTextChange, 
  onSend, 
  onGenerateSmartReplies,
  disabled = false 
}) => {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="input-container flex p-3 bg-gray-50 sticky bottom-0 w-fullborder-gray-200 focus:border-blue-500">
      <div className="flex-1 flex">
        <input
          type="text"
          value={text}
          onChange={(e) => onTextChange(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 p-2 border border-gray-300 rounded-l focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Type a message... (Press Enter to send)"
          disabled={disabled}
        />
        <button
          onClick={onGenerateSmartReplies}
          className="bg-purple-600 hover:bg-purple-700 text-white px-3 border-l-0 transition-colors"
          title="Get Smart Replies"
          disabled={disabled}
        >
          <Sparkles size={16} />
        </button>
      </div>
      <button
        onClick={onSend}
        disabled={!text.trim() || disabled}
        className="ml-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white p-2 rounded transition-colors"
      >
        <Send size={16} />
      </button>
    </div>
  );
};

export default MessageInput;