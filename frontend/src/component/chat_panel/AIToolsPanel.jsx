import React, { useEffect, useRef, useState } from 'react';
import { Languages, Zap, AlertCircle, CheckCircle } from 'lucide-react';
import socketService from "../services/socketServices";

const  AIToolsPanel = ({ 
  isVisible, 
  selectedLanguage, 
  onLanguageChange, 
  // onTranslate, 
  isTranslating, 
  enhancementType, 
  onEnhancementTypeChange, 
  // onEnhance, 
  isEnhancing, 
  hasText,
  inputText,
  setInputText // Add this prop to update the input text
}) => {
  const [showResult, setShowResult] = useState(false);
  const [resultMessage, setResultMessage] = useState('');
  const [resultType, setResultType] = useState('success'); // 'success' or 'error'

  const languages = [
    { code: "es", name: "Spanish" },
    { code: "fr", name: "French" },
    { code: "de", name: "German" },
    { code: "it", name: "Italian" },
    { code: "pt", name: "Portuguese" },
    // { code: "chinese", name: "Chinese" },
    // { code: "japanese", name: "Japanese" },
    // { code: "korean", name: "Korean" }
  ];
const onTranslate = (text, lang) => {
  return new Promise((resolve, reject) => {
    socketService.translateMessage(text, lang, (err, data) => {
      if (err) return reject(err);
      resolve(data);
    });
  });
};
  const handleTranslate = async () => {
    if (!hasText || !inputText.trim()) {
      showNotification('Please enter some text to translate', 'error');
   
      return;
    }

    try {
  setShowResult(false);
  const result = await onTranslate(inputText, selectedLanguage);
  console.log("Received result:", result);

  if (result && result.translated && result.translated !== inputText) {
    setInputText(result.translated);
    showNotification(`Translated to ${selectedLanguage}`, 'success');
  } else if (result && result.note) {
    showNotification(result.note, 'error');
  } else {
    showNotification('Translation failed or text unchanged', 'error');
  }
} catch (error) {
  console.error('Translation error:', error);
  showNotification('Translation failed', 'error');
}

  };
const onEnhance = (text, type) => {
  return socketService.enhanceMessage(text, type);
};

  const handleEnhance = async () => {
  if (!hasText || !inputText.trim()) {
    showNotification('Please enter some text to enhance', 'error');
    return;
  }

  try {
    setShowResult(false);
    const result = await onEnhance(inputText, enhancementType);
    console.log("Enhanced result:", result);

    if (result && result.enhanced && result.enhanced !== inputText) {
      setInputText(result.enhanced);
      showNotification(`Text enhanced (${enhancementType})`, 'success');
    } else {
      showNotification('Enhancement failed or no changes needed', 'error');
    }
  } catch (error) {
    console.error('Enhancement error:', error);
    showNotification('Enhancement failed', 'error');
  }
};

  const showNotification = (message, type) => {
    setResultMessage(message);
    setResultType(type);
    setShowResult(true);
    setTimeout(() => setShowResult(false), 3000);
  };

  if (!isVisible) return null;
//   const aiToolsRef = useRef(null);
// useEffect(() => {
//   if (showAITools && aiToolsRef.current) {
//     aiToolsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
//   }
// }, [showAITools]);
  return (
    <div className="bg-gray-700 p-3 border-b border-gray-600 relative">
      {/* Notification */}
      {showResult && (
        <div  className={`absolute top-16 left-0 right-0 bg-gray-700 p-3 border-b border-gray-600 z-20 shadow-lg ${
          resultType === 'success' 
            ? 'bg-green-600 text-white' 
            : 'bg-red-600 text-white'
        }`}>
          {resultType === 'success' ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
          {resultMessage}
        </div>
      )}

      {/* Translation Section */}
      <div className="flex flex-wrap gap-2 mb-3">
        <select
          value={selectedLanguage}
          onChange={(e) => onLanguageChange(e.target.value)}
          className="bg-gray-600 text-white p-1 rounded text-sm min-w-24"
        >
          {languages.map(lang => (
            <option key={lang.code} value={lang.code}>{lang.name}</option>
          ))}
        </select>
        <button
          onClick={handleTranslate}
          disabled={isTranslating || !hasText}
          className="bg-green-600 hover:bg-green-700 disabled:bg-gray-500 disabled:cursor-not-allowed text-white px-3 py-1 rounded text-sm flex items-center gap-1 transition-colors"
        >
          <Languages size={14} />
          {isTranslating ? 'Translating...' : 'Translate'}
        </button>
      </div>
      
      {/* Enhancement Section */}
      {/* <div className="flex flex-wrap gap-2">
        <select
          value={enhancementType}
          onChange={(e) => onEnhancementTypeChange(e.target.value)}
          className="bg-gray-600 text-white p-1 rounded text-sm min-w-32"
        >
          <option value="grammar">Fix Grammar</option>
          <option value="professional">Make Professional</option>
          <option value="casual">Make Casual</option>
        </select>
        <button
          onClick={handleEnhance}
          disabled={isEnhancing || !hasText}
          className="bg-orange-600 hover:bg-orange-700 disabled:bg-gray-500 disabled:cursor-not-allowed text-white px-3 py-1 rounded text-sm flex items-center gap-1 transition-colors"
        >
          <Zap size={14} />
          {isEnhancing ? 'Enhancing...' : 'Enhance'}
        </button>
      </div> */}
      
      {/* Debug Info (remove in production) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mt-2 text-xs text-gray-400">
          Debug: hasText={hasText.toString()}, textLength={inputText?.length || 0}
        </div>
      )}
    </div>
  );
};
export default AIToolsPanel;