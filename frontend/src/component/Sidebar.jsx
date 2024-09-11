import React, { useContext, useEffect, useState } from "react";
import { useUser, useUserUpdate } from "./context/UserContext";
import { useAuth } from "./context/AuthContext";
import io from 'socket.io-client';
import { ChatContext } from "./context/ChatContext";

const socket = io('http://localhost:5000'); // Adjust to your server URL
export default function Sidebar() {
  const [open, setOpen] = useState(true);
  const [users, setUsers] = useState([]);
  const [email, setEmail] = useState('');
  const user = useUser(); // Get the current user details

  const updateUser = useUserUpdate();
  const { data, dispatch } = useContext(ChatContext);

 

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/users`);
        const data = await response.json();
  
        setUsers(data)
   // Adjust this based on the actual structure of your API response
        console.log(users);
      } catch (error) {
        console.error("Error fetching users:", error);
      }
    };
  
    fetchUsers();
  
    const storedEmail = localStorage.getItem('Email');
    if (storedEmail) {
      setEmail(storedEmail);
    }
  
    // Listen for 'chat_session_created' event from the backend
    socket.on("chat_session_created", (response) => {
      const { chat_id } = response;
  
      // Dispatch action to update the context with the chatId
      if (user) {
        dispatch({ type: "User_Change", payload: { chatId: chat_id, user: user } });
      } else {
        console.warn("User is not defined when updating context.");
      }
    });
  
    // Clean up the listener on component unmount
    return () => {
      socket.off("chat_session_created");
    };
  }, [dispatch, user]);
  
  const handleUserClick = (selectedUser) => {
    updateUser(selectedUser);
  
    // Emit socket event to create a new chat session
    socket.emit('create_chat_session', {
      user1: email,
      user2: selectedUser.email
    });
  };
  return (
    <>
      <div
        className={`${
          open ? "w-1/6" : "w-20"
        } duration-300 h-auto p-5 pt-8 bg-slate-700 relative`}
      >
        <img
          src="./src/assets/left.png"
          alt=""
          className={`absolute cursor-pointer z-20 -right-3 top-9 w-8 border-2 border-slate-700 rounded-full bg-black ${
            !open && "rotate-180"
          }`}
          onClick={() => setOpen(!open)}
        />
        <div className="flex gap-x-4 items-center">
          <img
            src="./src/assets/logo1.png"
            className={`cursor-pointer duration-500 w-20 `}
            alt=""
            srcset=""
          />{" "}
          <h1
            className={`text-xl font-medium text-[#FBE6A3] origin-left duration-300 ${
              !open && "scale-0"
            }`}
          >
            InstaChat
          </h1>
        </div>
        <ul className="pt-6 max-w-md divide-y divide-gray-500 hover:divide-grey-300">
          {users.map(
            (user, index) =>
              
              user.email !== email && (
                <li
                key={index}
                className="flex text-gray-300 text-sm items-center gap-x-4 cursor-pointer p-2 hover:bg-light-white rounded-md "
                onClick={() => handleUserClick(user)}
                >
                  <img
                    className={`inline-block ${
                      open ? "h-12 w-12" : "h-6 w-6"
                    } duration-300 rounded-full ring-2 ring-[#FBE6A3]`}
                    src={`data:image/jpeg;base64,${user.profile_image}`}
                    alt=""
                  />
                  <span
                    className={`${!open && "hidden"} origin-left duration-200 font-medium text-lg	`}
                  >
                    {user.username}
                  </span>
                </li>
              )
          )}
        </ul>
      </div>
    </>
  );
}
