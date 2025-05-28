import React from 'react';

const Message = ({ message, currentUserId }) => {
  const isOwnMessage = message.sender_id === currentUserId;
  
  const getSentimentEmoji = (sentiment) => {
    if (!sentiment) return null;
    switch (sentiment.sentiment) {
      case 'positive': return '😊';
      case 'negative': return '😔';
      default: return '😐';
    }
  };

  const getSentimentColor = (sentiment) => {
    if (!sentiment) return 'border-gray-300';
    switch (sentiment.sentiment) {
      case 'positive': return 'border-green-400';
      case 'negative': return 'border-red-400';
      default: return 'border-yellow-400';
    }
  };

  return (
    <div className={`flex ${isOwnMessage ? "justify-end" : "justify-start"} mb-2`}>
      <div
        className={`p-3 rounded-lg max-w-xs lg:max-w-md relative ${
          isOwnMessage 
            ? `bg-blue-500 text-white ${getSentimentColor(message.ai_analysis?.sentiment)}` 
            : `bg-gray-100 text-gray-900 ${getSentimentColor(message.ai_analysis?.sentiment)}`
        } border-2`}
      >
        <div className="flex items-start justify-between">
          <p className="flex-1">{message.message}</p>
          {message.ai_analysis?.sentiment && (
            <span className="ml-2 text-sm">
              {getSentimentEmoji(message.ai_analysis.sentiment)}
            </span>
          )}
        </div>
        <div className="flex justify-between items-center mt-1">
          <span className="block text-xs opacity-75 text-gray-500">
            {new Date(message.timestamp).toLocaleString()}
          </span>
          {message.ai_analysis?.language && message.ai_analysis.language !== 'en' && (
            <span className="text-xs bg-black bg-opacity-20 px-1 rounded">
              {message.ai_analysis.language.toUpperCase()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default Message;