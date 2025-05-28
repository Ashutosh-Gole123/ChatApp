import React, { useEffect, useState } from "react";
import { useUser } from "./context/UserContext";
import { useAuth } from "./context/AuthContext";
import { useNavigate } from "react-router-dom";
import axios from 'axios';

export default function Header({sidebarVisible}) {
  const user = useUser();
  console.log(user);
  const {logout} = useAuth()
  const navigate = useNavigate()
    const [profile, setProfile] = useState({});

  const handleSubmit = () => {
    logout();
    navigate('/')
  }

  const [profileImage, setProfileImage] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Get email from localStorage
  const email = localStorage.getItem("Email");

  useEffect(() => {
    if (!email) {
      setLoading(false);
      return;
    }

    const fetchProfileImage = async () => {
      try {
        const response = await axios.get("http://localhost:5000/user/profile", {
          params: { email }
        });
        
        if (response.data && response.data.image) {
          setProfileImage(`${response.data.image}`);
        }
        setLoading(false);
      } catch (error) {
        console.error("Failed to load profile image:", error);
        setLoading(false);
      }
    };

    fetchProfileImage();
    
    // Set up event listener to reload when profile is updated
    window.addEventListener('storage', fetchProfileImage);
    
    return () => {
      window.removeEventListener('storage', fetchProfileImage);
    };
  }, [email]);

  if (loading) {
    return (
      <div className="w-10 h-10 rounded-full bg-gray-300 animate-pulse"></div>
    );
  }

  return (
    <>
      <div className={`flex  top-0 h-20 bg-slate-800 text-white p-3 z-10 transition-all duration-300 items-center justify-between  ${
        sidebarVisible ? "left-[250px] right-0" : "left-0 right-0"
      }`}>
  <div className="flex items-center gap-x-4">
    <img
      className="inline-block h-14 w-14 duration-300 rounded-full ring-2 ring-[#FBE6A3]"
      src={`data:image/jpeg;base64,${user.profile_image}`}
      alt=""
    />
    <h3 className="text-2xl">{user.username}</h3>
  </div>
  <div className="flex items-center gap-x-4">
        {/* Profile Avatar */}
      <img
      src={profileImage || "https://via.placeholder.com/150"}
      alt="Profile"
      onClick={() => navigate("/user/profile")}
      className="h-10 w-10 cursor-pointer rounded-full ring-2 ring-white hover:ring-[#FBE6A3] transition"
    />

        {/* Logout Button */}
        <button
          className="bg-slate-700 px-4 py-2 rounded hover:bg-slate-200 hover:text-gray-700 duration-300"
          type="button"
          onClick={handleSubmit}
        >
          Logout
        </button>
      </div>
</div>
    </>
  );
}
