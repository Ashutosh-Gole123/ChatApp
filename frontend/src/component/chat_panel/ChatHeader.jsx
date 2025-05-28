import React from 'react';
import { Sparkles, FileText } from 'lucide-react';

const ChatHeader = ({ onToggleAITools, onSummarizeConversation, showAITools }) => {
  return (
    <div className="bg-gray-800 p-3 sticky top-0 z-10 flex justify-between items-center">
  <h3 className="text-white font-semibold">Chat</h3>
  <div className="flex gap-2">
    <button
      onClick={onToggleAITools}
      className={`${
        showAITools ? 'bg-purple-700' : 'bg-purple-600 hover:bg-purple-700'
      } text-white p-2 rounded-full transition-colors`}
      title="AI Tools"
    >
      <Sparkles size={16} />
    </button>
    <button
      onClick={onSummarizeConversation}
      className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-full transition-colors"
      title="Summarize Conversation"
    >
      <FileText size={16} />
    </button>
  </div>
</div>
  );
};

export default ChatHeader;