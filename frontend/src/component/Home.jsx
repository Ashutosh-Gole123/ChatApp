import React, { useState } from "react";

import { UserProvider } from "./context/UserContext";
import Sidebar from "./Sidebar";
import Header from "./Header";
import ChatPanel from "./ChatPanel";
function Home() {
const sidebarVisible = true;

  return (
    <>
      <UserProvider>
        <div className="flex h-full w-full">
          {/* Sidebar */}
          <Sidebar className="w-1/4  bg-gray-800 text-white" />

          {/* Main Content Area */}
         <div className="flex flex-col w-5/6 h-screen overflow-hidden">
  <Header sidebarVisible={sidebarVisible} />
  <div className="flex-1 overflow-y-auto">
    <ChatPanel />
  </div>
</div>

        </div>
       
      </UserProvider>
    </>
  );
}

export default Home;
