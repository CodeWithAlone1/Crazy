import React, { useState } from "react";
import { ref, update } from "firebase/database";
import { updateProfile } from "firebase/auth";
import { database, auth } from "../firebase/config";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";
import { X, Camera, Save, User, Mail, FileText } from "lucide-react";

interface Props {
  onClose: () => void;
}

const UserProfileModal: React.FC<Props> = ({ onClose }) => {
  const { currentUser } = useAuth();
  const [displayName, setDisplayName] = useState(currentUser?.displayName || "");
  const [bio, setBio] = useState("Hey there! I am using FireChat.");
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!currentUser) return;
    if (!displayName.trim()) return toast.error("Name cannot be empty");
    setLoading(true);
    try {
      await updateProfile(auth.currentUser!, { displayName });
      await update(ref(database, `users/${currentUser.uid}`), {
        displayName,
        bio,
        photoURL: `https://api.dicebear.com/7.x/initials/svg?seed=${displayName}`,
      });
      toast.success("Profile updated!");
      onClose();
    } catch {
      toast.error("Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <h2 className="text-white font-bold text-lg">My Profile</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-xl transition-colors">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Avatar */}
          <div className="flex justify-center">
            <div className="relative">
              <img
                src={`https://api.dicebear.com/7.x/initials/svg?seed=${displayName || currentUser?.displayName}`}
                alt="Profile"
                className="w-24 h-24 rounded-full border-4 border-indigo-500"
              />
              <div className="absolute bottom-0 right-0 w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center border-2 border-gray-900">
                <Camera className="w-4 h-4 text-white" />
              </div>
            </div>
          </div>

          {/* Email (read-only) */}
          <div>
            <label className="text-gray-400 text-xs font-medium mb-1.5 flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5" /> Email
            </label>
            <div className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-xl text-gray-400 text-sm">
              {currentUser?.email}
            </div>
          </div>

          {/* Display Name */}
          <div>
            <label className="text-gray-400 text-xs font-medium mb-1.5 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5" /> Display Name
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white focus:outline-none focus:border-indigo-500 text-sm transition-colors"
            />
          </div>

          {/* Bio */}
          <div>
            <label className="text-gray-400 text-xs font-medium mb-1.5 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5" /> Bio
            </label>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              rows={3}
              maxLength={120}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white focus:outline-none focus:border-indigo-500 text-sm transition-colors resize-none"
            />
            <p className="text-gray-600 text-xs text-right mt-1">{bio.length}/120</p>
          </div>

          {/* Save Button */}
          <button
            onClick={handleSave}
            disabled={loading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            {loading ? "Saving..." : "Save Profile"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserProfileModal;
