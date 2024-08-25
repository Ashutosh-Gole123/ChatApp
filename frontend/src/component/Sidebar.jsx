import React, { useEffect, useState } from "react";
import { useUser,useUserUpdate } from "./context/UserContext";
export default function Sidebar() {
  const [open, setOpen] = useState(true);
  const [users, setUsers] = useState([]);
  const user = useUser()
  console.log(user);
  const updateUser = useUserUpdate()
  const fetchUsers = async () => {
    try {
      const response = await fetch(`https://jsonplaceholder.typicode.com/users`);
      const data = await response.json();

      // Update suggestions based on the fetched data
      setUsers(data); // Adjust this based on the actual structure of your API response
      console.log(users);
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);
  return (
    <>
      <div
        className={`${
          open ? "w-72" : "w-20"
        } duration-300 h-auto p-5 pt-8 bg-slate-700 relative`}
      >
        <img
          src="./src/assets/left.png"
          alt=""
          className={`absolute cursor-pointer -right-3 top-9 w-8 border-2 border-slate-700 rounded-full bg-black ${
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
        <ul className="pt-6">
          {users.map((user,index)=> (
            <li className="flex text-gray-300 text-sm items-center gap-x-4 cursor-pointer p-2 hover:bg-light-white rounded-md" onClick={()=>updateUser(user)}>
            <img
              className={`inline-block ${
                open ? "h-12 w-12" : "h-6 w-6"
              } duration-300 rounded-full ring-2 ring-[#FBE6A3]`}
              src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
              alt=""
            />
            <span className={`${!open && 'hidden'} origin-left duration-200`}>{user.name}</span>
          </li>
          ))}
        </ul>
      </div>
    </>
  );
}
