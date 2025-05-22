import { useState, useEffect } from "react";
import axios from 'axios';
import Header from "../Header";
import { UserProvider } from "../context/UserContext";
import { useAuth } from '../context/AuthContext'; // adjust path

export default function EditProfile() {
  const [profile, setProfile] = useState({
    name: "",
    email: "",
    image: null
  });
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const sidebarVisible = false;
  const { isAuthenticated } = useAuth();

  // Get email from localStorage
  const email = localStorage.getItem("Email");

  useEffect(() => {
    console.log("Fetching profile for email:", email);
    if (!email) {
      setError("Please log in first!");
      setLoading(false);
      return;
    }

    axios
      .get("http://localhost:5000/user/profile", {
        params: { email }
      })
      .then(res => {
        console.log("Profile data received:", res.data);
        setProfile({
          name: res.data.name || "",
          email: res.data.email || "",
          image: null // Don't preload the file input
        });

        // Set image preview if available
        if (res.data.image) {
          setPreview(`${res.data.image}`);
          console.log("Image preview set");
        } else {
          console.log("No image data in response");
          setPreview(null);
        }
        setLoading(false);
      })
      .catch(error => {
        console.error("Failed to load user profile:", error);
        setError("Could not load profile. Please try again.");
        setLoading(false);
      });
  }, [email]);

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    if (files && files.length > 0) {
      const file = files[0];
      setProfile(prev => ({ ...prev, [name]: file }));
      setPreview(URL.createObjectURL(file));
    } else {
      setProfile(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      setError('Please log in first!');
      return;
    }

    try {
      // Create FormData object to handle file uploads
      const formData = new FormData();
      formData.append('name', profile.name);
      formData.append('email', profile.email);
      
      // Only append image if it exists
      if (profile.image) {
        formData.append('image', profile.image);
      }

      setLoading(true);
      const response = await axios.put('http://localhost:5000/user/profile', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      console.log('Profile updated:', response.data);
      setSuccess(true);
      
      // Update email in localStorage if it changed
      if (email !== profile.email) {
        localStorage.setItem("Email", profile.email);
      }
      
      setLoading(false);
      
      // Reload the page to reflect changes
      setTimeout(() => {
        window.location.reload();
      }, 1000);
      
    } catch (error) {
      console.error('Error updating profile:', error);
      setError(error.response?.data?.error || 'Failed to update profile');
      setLoading(false);
    }
  };

  if (loading && !profile.name) {
    return (
      <UserProvider>
        <div className="flex flex-col h-full w-full">
          <Header sidebarVisible={sidebarVisible} />
          <div className="mt-24 flex justify-center">
            <p>Loading profile...</p>
          </div>
        </div>
      </UserProvider>
    );
  }

  return (
    <UserProvider>
      <div className="flex flex-col h-full w-full">
        <Header sidebarVisible={sidebarVisible} />

        {/* Spacer below header */}
        <div className="mt-24 px-4 flex justify-center">
          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-6 w-full max-w-md p-6 bg-slate-400 rounded-lg shadow-md"
          >
            {error && (
              <div className="bg-red-500 text-white p-3 rounded-lg">
                {error}
              </div>
            )}
            
            {success && (
              <div className="bg-green-500 text-white p-3 rounded-lg">
                Profile updated successfully!
              </div>
            )}

            {/* Profile image with edit button */}
            <div className="relative w-32 h-32 mx-auto">
              <img
src={preview || "https://via.placeholder.com/150"}
                alt="Profile"
                className="w-32 h-32 rounded-full object-cover border-2 border-blue-500 shadow-sm"
              />
              <label className="absolute bottom-0 right-0 bg-blue-600 text-white px-3 py-1 text-sm rounded-full cursor-pointer hover:bg-blue-700 transition">
                Edit
                <input
                  type="file"
                  name="image"
                  accept="image/*"
                  onChange={handleChange}
                  className="hidden"
                />
              </label>
            </div>

            <input
              name="name"
              value={profile.name}
              onChange={handleChange}
              placeholder="Name"
              className="px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
              required
            />

            <input
              name="email"
              value={profile.email}
              onChange={handleChange}
              placeholder="Email"
              type="email"
              className="px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
              required
            />

            <button
              type="submit"
              disabled={loading}
              className={`${
                loading ? 'bg-gray-500' : 'bg-blue-600 hover:bg-blue-700'
              } text-white font-semibold px-6 py-3 rounded-lg shadow-md transition`}
            >
              {loading ? 'Updating...' : 'Update'}
            </button>
          </form>
        </div>
      </div>
    </UserProvider>
  );
}