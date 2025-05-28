import React from 'react';
import { MessageSquare } from 'lucide-react';

const SmartReplies = ({ replies, onReplyClick, isVisible }) => {
  if (!isVisible || replies.length === 0) return null;

  return (
    <div className="bg-gray-700 p-3 border-t border-gray-600">
      <div className="flex items-center gap-2 mb-2">
        <MessageSquare size={16} className="text-purple-400" />
        <span className="text-white text-sm">Smart Replies:</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {replies.map((reply, index) => (
          <button
            key={index}
            onClick={() => onReplyClick(reply)}
            className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded-full text-sm transition-colors"
          >
            {reply}
          </button>
        ))}
      </div>
    </div>
  );
};

export default SmartReplies;