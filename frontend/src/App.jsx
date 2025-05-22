import React, { useState, useEffect } from "react";
import io from "socket.io-client";
import Register from "./component/Register";
import Login from "./component/Login";
import Home from "./component/Home";
import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "./component/ProtectedRoute";
// const socket = io('http://localhost:5000'); // Adjust if your Flask server is on a different host or port
import { useAuth } from "./component/context/AuthContext";
import EditProfile from "./component/profile/editProfile";
function App() {
 
  const { isAuthenticated } = useAuth();
  
  return (
    <>
      <Routes>
        {!isAuthenticated ? (
          <>
            <Route path="/" element={<Register />} />
            <Route path="/login" element={<Login />} />{" "}
          </>
        ) : (
          <>
            <Route
              path="/home"
              element={<ProtectedRoute element={<Home />} />}
            />
            <Route
              path="/user/profile"
              element={<ProtectedRoute element={<EditProfile />} />}
            />
            <Route path="*" element={<Navigate to="/home" />} />{" "}
            {/* Redirect unknown routes */}
          </>
        )}
      </Routes>
    </>
    // <div>
    //   <h1>Chat Room</h1>
    //   <input
    //     type="text"
    //     placeholder="Enter your name"
    //     value={username}
    //     onChange={(e) => setUsername(e.target.value)}
    //   />
    //   <button onClick={addUser}>Add User</button>
    //   <br />
    //   <h2>Users List</h2>
    //   <ul>
    //     {userList.map((user, index) => (
    //       <li key={index} onClick={() => createRoomFromUser(user)}>
    //         {user}
    //       </li>
    //     ))}
    //   </ul>
    //   {activeRoom && (
    //     <div>
    //       <h2>Room: {activeRoom}</h2>
    //       <button onClick={leaveRoom}>Leave Room</button>
    //       <br />
    //       <input
    //         type="text"
    //         placeholder="Your message"
    //         value={message}
    //         onChange={(e) => setMessage(e.target.value)}
    //       />
    //       <button onClick={sendMessage}>Send</button>
    //       <ul>
    //         {messages.map((msg, index) => (
    //           <li key={index}>{msg}</li>
    //         ))}
    //       </ul>
    //     </div>
    //   )}
    // </div>
  );
}

export default App;

// import { useState } from "react";
// import { Route, Routes, Link } from "react-router-dom";
// import "./App.css";
// import { UserProvider } from "./component/context/UserContext";
// import Sidebar from "./component/Sidebar";
// import Header from "./component/Header";
// import io from 'socket.io-client';

// const socket = io('http://localhost:5000');

// function App() {
//   const [room, setRoom] = useState('');
//   const [username, setUsername] = useState('');
//   const [message, setMessage] = useState('');
//   const [messages, setMessages] = useState([]);

//   useEffect(() => {
//     socket.on('message', (msg) => {
//       setMessages((prevMessages) => [...prevMessages, msg]);
//     });

//     // Cleanup on unmount
//     return () => {
//       socket.off('message');
//     };
//   }, []);

//   const joinRoom = () => {
//     if (room && username) {
//       socket.emit('join', { username, room });
//     }
//   };

//   const leaveRoom = () => {
//     if (room && username) {
//       socket.emit('leave', { username, room });
//     }
//   };

//   const sendMessage = () => {
//     if (room && message) {
//       socket.emit('message', { room, message });
//       setMessage(''); // Clear the input field after sending
//     }
//   };

//   return (
//     <>
//     <UserProvider>
//     <div className="flex">
//           <Sidebar/>
//            <Header/>
//       </div>
//     </UserProvider>

// //       {/* <nav>
// //         <ul>
// //           <li><Link to="/">Sidebar</Link></li>
// //           <li><Link to="/about">About</Link></li>
// //           <li><Link to="/contact">Contact</Link></li>
// //         </ul>
// //       </nav> */}
// //       {/* <Routes>
// //         <Route path="/" element={<Home />} />
// //         <Route path="/about" element={<About />} />
// //         <Route path="/contact" element={<Contact />} />
// //       </Routes> */}

//     </>
//   );
// }

// export default App;

//   return (
//     <div>
//       <h1>Chat Room</h1>
//       <input
//         type="text"
//         placeholder="Room name"
//         value={room}
//         onChange={(e) => setRoom(e.target.value)}
//       />
//       <input
//         type="text"
//         placeholder="Username"
//         value={username}
//         onChange={(e) => setUsername(e.target.value)}
//       />
//       <button onClick={joinRoom}>Join Room</button>
//       <button onClick={leaveRoom}>Leave Room</button>
//       <br />
//       <input
//         type="text"
//         placeholder="Your message"
//         value={message}
//         onChange={(e) => setMessage(e.target.value)}
//       />
//       <button onClick={sendMessage}>Send</button>
//       <ul>
//         {messages.map((msg, index) => (
//           <li key={index}>{msg}</li>
//         ))}
//       </ul>
//     </div>
//   );
// }

// export default App;
