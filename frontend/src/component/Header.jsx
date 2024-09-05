import React from "react";
import { useUser } from "./context/UserContext";
import { useAuth } from "./context/AuthContext";
import { useNavigate } from "react-router-dom";
export default function Header() {
  const user = useUser();
  const {logout} = useAuth()
  const navigate = useNavigate()
  const handleSubmit = () => {
    logout();
    navigate('/')
  }
  return (
    <>
      <div className="flex-1 flex h-20 bg-slate-600 items-center justify-between text-white p-3 fixed w-5/6">
  <div className="flex items-center gap-x-4">
    <img
      className="inline-block h-14 w-14 duration-300 rounded-full ring-2 ring-[#FBE6A3]"
      src={`data:image/jpeg;base64,${user.profile_image}`}
      alt=""
    />
    <h3 className="text-2xl">{user.username}</h3>
  </div>
  
  <button className="bg-slate-700 p-3 rounded hover:bg-slate-200 hover:text-gray-700 duration-300" type="button" onClick={handleSubmit}>
    Logout
  </button>
</div>
    </>
  );
}
