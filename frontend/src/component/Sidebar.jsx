import React, { useContext, useEffect, useState, useMemo, useCallback, useRef } from "react";
import { useUser, useUserUpdate } from "./context/UserContext";
import { useAuth } from "./context/AuthContext";
import io from 'socket.io-client';
import { ChatContext } from "./context/ChatContext";

// Create socket connection outside component to prevent recreation on re-renders
const socket = io('http://localhost:5000');

export default function Sidebar() {
  const [open, setOpen] = useState(true);
  const [allUsers, setAllUsers] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [email, setEmail] = useState('');
  const [chatId, setChatId] = useState('');
  const [showContactModal, setShowContactModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [contactsData, setContactsData] = useState({});
  
  // Ref to store latest contacts for socket access
  const contactsRef = useRef([]);
  const contactsDataRef = useRef({});
  
  // Update refs when state changes
  useEffect(() => {
    contactsRef.current = contacts;
  }, [contacts]);
  
  useEffect(() => {
    contactsDataRef.current = contactsData;
  }, [contactsData]);
  
  const user = useUser();
  const updateUser = useUserUpdate();
  const { data, dispatch } = useContext(ChatContext);
  
  // Helper function to ensure reliable contactsData updates
  const updateContactData = useCallback((contactEmail, updates) => {
    setContactsData(prev => {
      // Create a fresh object - this ensures React detects the change
      const newState = {...prev};
      
      // Create or update the contact entry
      newState[contactEmail] = {
        ...(newState[contactEmail] || {}),
        ...updates,
        // Force timestamp update to always trigger sorts on state change
        _lastUpdated: Date.now()
      };
      
      console.log(`Updated contact ${contactEmail} with:`, updates);
      return newState;
    });
  }, []);
  
  // Sequence loading to ensure proper data relationships
  useEffect(() => {
    const storedEmail = localStorage.getItem('Email');
    if (!storedEmail) return;
    
    setEmail(storedEmail);
    
    const fetchAllData = async () => {
      try {
        // First fetch users
        const usersResponse = await fetch(`http://localhost:5000/api/users`);
        const usersData = await usersResponse.json();
        setAllUsers(usersData.users || []);
        
        // Then fetch contacts
        const contactsResponse = await fetch(`http://localhost:5000/api/contacts/${storedEmail}`);
        const contactsData = await contactsResponse.json();
        const contactList = contactsData.contacts || [];
        setContacts(contactList);
        contactsRef.current = contactList;
        
        // Initialize contactsData with empty entries for each contact
        const initialContactsData = {};
        contactList.forEach(contact => {
          initialContactsData[contact.email] = {
            lastMessageTime: 0,
            lastMessage: '',
            unreadCount: 0
          };
        });
        
        // Then fetch latest messages
        const lastMessagesResponse = await fetch(`http://localhost:5000/api/last-messages/${storedEmail}`);
        const lastMessagesData = await lastMessagesResponse.json();
        
        if (lastMessagesData.status === 'success') {
          lastMessagesData.messages.forEach(msg => {
            if (initialContactsData[msg.email]) {
              initialContactsData[msg.email] = {
                lastMessageTime: new Date(msg.timestamp).getTime(),
                lastMessage: msg.message || '',
                unreadCount: msg.unread || 0
              };
            }
          });
        }
        
        console.log("Initial contact data loaded:", initialContactsData);
        setContactsData(initialContactsData);
        contactsDataRef.current = initialContactsData;
        
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };
    
    fetchAllData();
  }, []);
  
  // Set up socket listeners - using refs for latest state access
  useEffect(() => {
    if (!email) return;
    
    const handleReceiveMessage = (messageData) => {
      console.log("Received message:", messageData);
      dispatch({ type: "New_Message", payload: messageData });
      
      const { sender_id, timestamp, message_text } = messageData;
      
      // Access the latest contacts via ref
      const currentContacts = contactsRef.current;
      const contact = currentContacts.find(c => c.user_id === sender_id);
      
      if (contact) {
        console.log("Found contact for message:", contact.email);
        
        // Force update to contactsData with proper data
        setContactsData(prev => {
          const newState = {...prev};
          
          // Create new entry or update existing one
          newState[contact.email] = {
            ...newState[contact.email],
            lastMessageTime: new Date(timestamp).getTime(), // Convert to number
            lastMessage: message_text || '',
            unreadCount: ((newState[contact.email]?.unreadCount || 0) + 1),
            _forceUpdate: Date.now() // Force React to detect change
          };
          
          return newState;
        });
      }
    };
    
    const handleChatSessionCreated = (response) => {
      const { chat_id } = response;
      setChatId(chat_id);
      
      if (user) {
        dispatch({ type: "User_Change", payload: { chatId: chat_id, user: user } });
      }
      
      socket.emit('join_room', { chat_id });
    };
    
    const handleNewContactAdded = (data) => {
      if (data.contactEmail === email) {
        // Fetch latest contacts list
        fetch(`http://localhost:5000/api/contacts/${email}`)
          .then(res => res.json())
          .then(data => {
            const contacts = data.contacts || [];
            setContacts(contacts);
            contactsRef.current = contacts;
            
            // Initialize contactsData for new contacts
            setContactsData(prev => {
              const updated = {...prev};
              contacts.forEach(contact => {
                if (!updated[contact.email]) {
                  updated[contact.email] = {
                    lastMessageTime: 0,
                    lastMessage: '',
                    unreadCount: 0
                  };
                }
              });
              return updated;
            });
          })
          .catch(err => console.error("Error fetching contacts:", err));
      }
    };
    
    // Register handlers with named functions for proper cleanup
    socket.on("receive_message", handleReceiveMessage);
    socket.on("chat_session_created", handleChatSessionCreated);
    socket.on("new_contact_added", handleNewContactAdded);
    
    // Clean up all handlers
    return () => {
      socket.off("receive_message", handleReceiveMessage);
      socket.off("chat_session_created", handleChatSessionCreated);
      socket.off("new_contact_added", handleNewContactAdded);
    };
  }, [email, dispatch, user]);
  
  // Enhanced sorting with error handling and useMemo for performance
  const sortedContacts = useMemo(() => {
    console.log("Sorting contacts with data:", contactsData);
    
    if (!contacts || contacts.length <= 1) return contacts;
    
    try {
      return [...contacts].sort((a, b) => {
        // Get numeric timestamps with fallbacks
        const getTime = (contact) => {
          const data = contactsData[contact.email];
          if (!data || !data.lastMessageTime) return 0;
          
          const timestamp = data.lastMessageTime;
          // Handle both string dates and numbers
          if (typeof timestamp === 'string') {
            const time = new Date(timestamp).getTime();
            return isNaN(time) ? 0 : time;
          }
          return timestamp;
        };
        
        const timeA = getTime(a);
        const timeB = getTime(b);
        
        // Log sorting decisions for debugging
        if (timeA === 0 && timeB === 0) {
          console.log(`Both ${a.email} and ${b.email} have no timestamps`);
        } else {
          console.log(`Comparing ${a.email}(${timeA}) with ${b.email}(${timeB})`);
        }
        
        // Sort by timestamp (latest first)
        return timeB - timeA;
      });
    } catch (err) {
      console.error("Error sorting contacts:", err);
      return [...contacts]; // Return unsorted on error
    }
  }, [contacts, contactsData]);
  
  // Enhanced user filtering with useMemo
  const filteredUsers = useMemo(() => {
    if (searchTerm.trim() === '') return [];
    
    return allUsers.filter(
      user => 
        user.email !== email && 
        !contacts.some(contact => contact.email === user.email) &&
        (user.username.toLowerCase().includes(searchTerm.toLowerCase()) || 
        user.email.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  }, [searchTerm, allUsers, contacts, email]);
  
  // Use our helper for reliable updates
  const handleUserClick = useCallback((selectedUser) => {
    updateUser(selectedUser);
    
    // Reset unread with our reliable helper
    updateContactData(selectedUser.email, { unreadCount: 0 });
    
    socket.emit('create_chat_session', {
      user1: email,
      user2: selectedUser.email
    });
  }, [email, updateUser, updateContactData]);
  
 
  
  // Use callbacks for add/remove contact functions
  const addContact = useCallback(async (userToAdd) => {
    try {
      const response = await fetch('http://localhost:5000/api/contacts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userEmail: email,
          contactEmail: userToAdd.email
        }),
      });
      
      if (response.ok) {
        setContacts(prevContacts => [...prevContacts, userToAdd]);
        setSearchTerm('');
        
        socket.emit('add_contact_notification', {
          userEmail: email,
          contactEmail: userToAdd.email,
          contactDetails: userToAdd
        });
      } else {
        console.error('Failed to add contact');
      }
    } catch (error) {
      console.error('Error adding contact:', error);
    }
  }, [email]);
  
  const removeContact = useCallback(async (contactEmail) => {
    try {
      const response = await fetch('http://localhost:5000/api/contacts', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userEmail: email,
          contactEmail
        }),
      });
      
      if (response.ok) {
        setContacts(prevContacts => 
          prevContacts.filter(contact => contact.email !== contactEmail)
        );
        
        socket.emit('remove_contact_notification', {
          userEmail: email,
          contactEmail
        });
      } else {
        console.error('Failed to remove contact');
      }
    } catch (error) {
      console.error('Error removing contact:', error);
    }
  }, [email]);
  
  // Rest of your component (JSX) remains the same
  
  return (
    <>
      <div
        className={`${
          open ? "w-1/6" : "w-20"
        } duration-300 h-auto p-5 pt-8 bg-slate-900 relative`}
      >
        {/* Toggle button and UI elements */}
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
          />{" "}
          <h1
            className={`text-xl font-medium text-[#FBE6A3] origin-left duration-300 ${
              !open && "scale-0"
            }`}
          >
            InstaChat
          </h1>
        </div>

        {/* Contact management buttons */}
        {open && (
          <div className="flex justify-between mt-4 mb-2">
            <h2 className="text-[#FBE6A3] font-medium">Contacts</h2>
            <button 
              className="bg-[#FBE6A3] text-slate-700 px-2 py-1 rounded text-sm"
              onClick={() => setShowContactModal(true)}
            >
              Add
            </button>
          </div>
        )}

        {/* Contact list */}
        <ul className="pt-2 max-w-md divide-y border-slate-700 hover:divide-grey-300">
          {contacts.length === 0 ? (
            <li className="text-slate-100 text-sm p-2">No contacts yet</li>
          ) : (
            sortedContacts.map((contact, index) => (
              <li
                key={index}
                className="flex text-slate-100 items-center gap-x-2 cursor-pointer p-2 hover:bg-slate-800 rounded-md"
              >
                <img
                  className={`inline-block ${
                    open ? "h-10 w-10" : "h-6 w-6"
                  } duration-300 rounded-full ring-2 ring-[#FBE6A3]`}
                  src={`data:image/jpeg;base64,${contact.profile_image}`}
                  alt=""
                  onClick={() => handleUserClick(contact)}
                />
                {open && (
                  <>
                    <span
                      className="origin-left duration-200 font-medium text-lg flex-grow"
                      onClick={() => handleUserClick(contact)}
                    >
                      {contact.username}
                    </span>
                    {contactsData[contact.email]?.unreadCount > 0 && (
                      <span className="ml-2 text-xs bg-red-500 text-white rounded-full px-2">
                        {contactsData[contact.email].unreadCount}
                      </span>
                    )}

                    <button 
                      className="text-red-400 text-sm hover:text-red-600"
                      onClick={() => removeContact(contact.email)}
                    >
                      ✕
                    </button>
                  </>
                )}
              </li>
            ))
          )}
        </ul>
      </div>

      {/* Add Contact Modal */}
      {showContactModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-slate-800 p-4 rounded-lg w-96">
            <h2 className="text-[#FBE6A3] text-lg font-medium mb-4">Add New Contact</h2>
            
            <div className="mb-4">
              <input
                type="text"
                placeholder="Search by name or email"
                className="w-full p-2 rounded bg-slate-700 text-white"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            <div className="max-h-60 overflow-y-auto">
              {filteredUsers.length > 0 ? (
                filteredUsers.map((user, index) => (
                  <div 
                    key={index}
                    className="flex items-center gap-2 p-2 hover:bg-slate-700 rounded cursor-pointer"
                    onClick={() => addContact(user)}
                  >
                    <img
                      className="h-8 w-8 rounded-full ring-1 ring-[#FBE6A3]"
                      src={`data:image/jpeg;base64,${user.profile_image}`}
                      alt=""
                    />
                    <div>
                      <p className="text-white">{user.username}</p>
                      <p className="text-gray-400 text-sm">{user.email}</p>
                    </div>
                  </div>
                ))
              ) : (
                searchTerm.trim() !== '' && (
                  <p className="text-gray-300 text-center py-2">No users found</p>
                )
              )}
              
              {searchTerm.trim() === '' && (
                <p className="text-gray-300 text-center py-2">Type to search for users</p>
              )}
            </div>
            
            <div className="mt-4 flex justify-end">
              <button 
                className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
                onClick={() => {
                  setShowContactModal(false);
                  setSearchTerm('');
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}