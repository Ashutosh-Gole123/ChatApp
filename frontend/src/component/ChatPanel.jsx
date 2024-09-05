import React, { useContext } from "react";
import { ChatContext } from "./context/ChatContext";
import Input from "./Input";

function ChatPanel() {
  const { data } = useContext(ChatContext); 

  return (
    <>
      <div className="relative h-screen w-full mt-20 bg-zinc-600">
        <h1 className="absolute top-10 w-auto bg-slate-400 text-white p-3 rounded-r-lg">{data.chatId}</h1>
        <h1 className="absolute top-20 w-auto bg-slate-400 text-white p-3 right-0 rounded-l-lg">Hii</h1> 
<Input/>
      </div>
    </>
  );
}

export default ChatPanel;
