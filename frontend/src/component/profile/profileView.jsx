import { useState, useEffect } from 'react';
import axios from 'axios';

// This component handles profile image display with cache busting
const ProfileImage = ({ email, className, size = 'md' }) => {
  const [imageData, setImageData] = useState(null);
  const [timestamp, setTimestamp] = useState(Date.now());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Size classes
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
    xl: 'w-24 h-24',
    '2xl': 'w-32 h-32'
  };

  const fetchProfileImage = async () => {
    if (!email) return;
    
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:5000/user/profile', {
        params: { 
          email,
          timestamp: Date.now() // Prevent caching
        }
      });
      
      if (response.data && response.data.image) {
        setImageData(response.data.image);
        setTimestamp(response.data.timestamp || Date.now());
      }
      setLoading(false);
    } catch (err) {
      console.error('Error fetching profile image:', err);
      setError(err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfileImage();
    
    // Listen for profile update events
    const handleProfileUpdate = (event) => {
      if (event.detail.email === email) {
        fetchProfileImage();
      }
    };
    
    window.addEventListener('profileUpdated', handleProfileUpdate);
    
    return () => {
      window.removeEventListener('profileUpdated', handleProfileUpdate);
    };
  }, [email]);

  // Listen for storage events (if email is updated in another tab)
  useEffect(() => {
    const handleStorageChange = () => {
      fetchProfileImage();
    };
    
    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  if (loading) {
    return (
      <div className={`${sizeClasses[size]} ${className} rounded-full bg-gray-300 animate-pulse`}></div>
    );
  }

  if (error || !imageData) {
    // Fallback to placeholder
    return (
      <div className={`${sizeClasses[size]} ${className} rounded-full bg-blue-400 flex items-center justify-center text-white font-bold`}>
        {email ? email.charAt(0).toUpperCase() : '?'}
      </div>
    );
  }

  return (
    <img
      src={`data:image/jpeg;base64,${imageData.split('?')[0]}?v=${timestamp}`}
      alt="Profile"
      className={`${sizeClasses[size]} ${className} rounded-full object-cover`}
      key={timestamp} // Force React to re-render when timestamp changes
      onError={(e) => {
        e.target.onerror = null;
        e.target.src = "https://via.placeholder.com/150";
      }}
    />
  );
};

export default ProfileImage;