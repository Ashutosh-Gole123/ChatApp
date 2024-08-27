import React, { useState } from "react";

import { UserProvider } from "./context/UserContext";
import Sidebar from "./Sidebar";
import Header from "./Header";
function Home() {
  return (
    <>
      <UserProvider>
        <div className="flex h-auto">
          {/* Sidebar */}
          <Sidebar className="w-1/4  bg-gray-800 text-white" />

          {/* Main Content Area */}
          <div className="flex flex-col w-3/4">
            {/* Header */}
            <Header className=" bg-gray-900 text-white" />

            {/* Content */}
            <div className="flex-grow mt-20">
              <h1 className="w-20 bg-slate-400 text-white p-3">Hello</h1>
            </div>
          </div>
        </div>
      </UserProvider>
    </>
  );
}

export default Home;
