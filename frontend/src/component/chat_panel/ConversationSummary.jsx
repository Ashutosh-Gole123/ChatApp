import React from 'react';
import { X } from 'lucide-react';

const ConversationSummary = ({ isVisible, summary, onClose }) => {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg max-w-lg mx-4 max-h-96 overflow-y-auto relative">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-bold">Conversation Summary</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        <div className="text-gray-700 mb-4">
          {summary ? (
            <p>{summary}</p>
          ) : (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-2">Generating summary...</span>
            </div>
          )}
        </div>
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConversationSummary;