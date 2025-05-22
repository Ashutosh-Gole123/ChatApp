import React,{createContext, useContext, useState } from "react";


const UserContext = createContext()
const UserUpdateContext = createContext()

export function useUser(){
    return useContext(UserContext)
} 

export function useUserUpdate(){
    return useContext(UserUpdateContext)
} 

export function UserProvider({children}){
    const [currUser, setCurrUser] = useState({
        name: '',
        email: '',
        profile: ''
        // Add other user details here
      });
    function updateUser(newUserDetails){
        setCurrUser(newUserDetails)
    }
    return(
        <UserContext.Provider value={currUser}>
            <UserUpdateContext.Provider value={updateUser}>
            {children}
            </UserUpdateContext.Provider>
        </UserContext.Provider>
    )
}
