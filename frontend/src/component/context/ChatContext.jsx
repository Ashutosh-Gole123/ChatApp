import { createContext, useReducer, useEffect } from "react";

// Create the ChatContext
export const ChatContext = createContext();

// Initial state for one-to-one chat
const INITIAL_STATE = {
  chatId: "null", // Default value when no chat is selected
  user: {},       // Object to store the selected user's information
};

// Reducer function to handle state updates
const reducer = (state, action) => {
  switch (action.type) {
    case "User_Change": {
      const selectedUser = action.payload.user; // Extract user from the payload
      const chatId = action.payload.chatId || "null"; // Use chatId from payload or default

      // Return the updated state
      return {
        ...state,
        user: selectedUser,
        chatId,
      };
    }
    default:
      return state; // Return the unchanged state for any unknown actions
  }
};

// ChatContextProvider component to wrap your application
export const ChatContextProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE); // useReducer hook to manage state

  

  return (
    <ChatContext.Provider value={{ data: state, dispatch }}>
      {children}
    </ChatContext.Provider>
  );
};
