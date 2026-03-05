import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getDatabase } from "firebase/database";

// 🔥 REPLACE THESE WITH YOUR FIREBASE CONSOLE API KEYS
// Go to: https://console.firebase.google.com
// Project Settings → Your Apps → SDK Setup → Config
const firebaseConfig = {
  apiKey: "AIzaSyByDSBzWpaJn6gO9mP6fXYf_sphzAGqYnM",
  authDomain: "chatting-app-5bd41.firebaseapp.com",
  databaseURL: "https://chatting-app-5bd41-default-rtdb.firebaseio.com",
  projectId: "chatting-app-5bd41",
  storageBucket: "chatting-app-5bd41.firebasestorage.app",
  messagingSenderId: "786070124809",
  appId: "1:786070124809:web:bf0aaa4d92e814d7b43bd8",
  measurementId: "G-VV36ZND93T"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const database = getDatabase(app);
export default app;
