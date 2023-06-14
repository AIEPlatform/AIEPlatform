import { createContext, useState, useEffect } from "react";
export const UserContext = createContext(null);

function UserContextWrapper({ children }) {
    const [userContext, sUserContext] = useState(undefined);
    useEffect(() => {
        fetch('/apis/auth/currentUser')
            .then(res => res.json())
            .then(data => {
                if (data['status'] === 200) {
                    sUserContext(data['user']);
                }
                else {
                    sUserContext(null);
                }
            })
    }, []);

    return (
        <UserContext.Provider value={{ userContext, sUserContext }}>
            {children}
        </UserContext.Provider>
    );
}

export default UserContextWrapper;