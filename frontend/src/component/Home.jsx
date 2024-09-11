import React, { useState } from "react";

import { UserProvider } from "./context/UserContext";
import Sidebar from "./Sidebar";
import Header from "./Header";
import ChatPanel from "./ChatPanel";
function Home() {
  return (
    <>
      <UserProvider>
        <div className="flex h-full w-full">
          {/* Sidebar */}
          <Sidebar className="w-1/4  bg-gray-800 text-white" />

          {/* Main Content Area */}
          <div className="flex h-full w-5/6">
            {/* Header */}
            <Header className=" bg-gray-900 text-white" />

            {/* Content */}
              <ChatPanel className="flex "/>
          </div>
        </div>
      </UserProvider>
    </>
  );
}

export default Home;
