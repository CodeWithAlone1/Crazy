import React, { createContext, useContext, useEffect, useState } from "react";
import {
  User,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  updateProfile,
} from "firebase/auth";
import { ref, set, onValue, serverTimestamp } from "firebase/database";
import { auth, database } from "../firebase/config";

interface AuthContextType {
  currentUser: User | null;
  loading: boolean;
  signup: (email: string, password: string, displayName: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const signup = async (email: string, password: string, displayName: string) => {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    await updateProfile(userCredential.user, { displayName });
    // Save user profile to database
    await set(ref(database, `users/${userCredential.user.uid}`), {
      uid: userCredential.user.uid,
      displayName,
      email,
      photoURL: `https://api.dicebear.com/7.x/initials/svg?seed=${displayName}`,
      createdAt: serverTimestamp(),
      online: true,
      lastSeen: serverTimestamp(),
      bio: "Hey there! I am using FireChat.",
    });
  };

  const login = async (email: string, password: string) => {
    await signInWithEmailAndPassword(auth, email, password);
  };

  const logout = async () => {
    if (currentUser) {
      await set(ref(database, `users/${currentUser.uid}/online`), false);
      await set(ref(database, `users/${currentUser.uid}/lastSeen`), serverTimestamp());
    }
    await signOut(auth);
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setCurrentUser(user);
      setLoading(false);
      if (user) {
        // Set user online
        set(ref(database, `users/${user.uid}/online`), true);
        set(ref(database, `users/${user.uid}/lastSeen`), serverTimestamp());

        // Set offline when disconnected
        const connectedRef = ref(database, ".info/connected");
        onValue(connectedRef, (snap) => {
          if (snap.val() === true) {
            set(ref(database, `users/${user.uid}/online`), true);
          }
        });
      }
    });
    return unsubscribe;
  }, []);

  return (
    <AuthContext.Provider value={{ currentUser, loading, signup, login, logout }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
