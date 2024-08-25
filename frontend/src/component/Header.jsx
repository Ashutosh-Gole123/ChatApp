import React from "react";
import { useUser } from "./context/UserContext";
export default function Header() {
  const user = useUser();
  return (
    <>
      <div className="flex-1 flex h-20 bg-slate-600 items-center gap-x-4 text-white p-3">
        <img
          className={`inline-block h-14 w-14 duration-300 rounded-full ring-2 ring-[#FBE6A3]`}
          src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
          alt=""
        />
        <h3 className="text-2xl">{user.name}</h3>
      </div>
    </>
  );
}
