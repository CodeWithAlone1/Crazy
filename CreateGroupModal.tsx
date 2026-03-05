import React, { useState } from "react";
import { ref, push, set, serverTimestamp } from "firebase/database";
import { database } from "../firebase/config";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";
import { X, Users, Check, Search, Hash } from "lucide-react";

interface UserData {
  uid: string;
  displayName: string;
  email: string;
  photoURL: string;
  online: boolean;
}

interface Props {
  allUsers: UserData[];
  onClose: () => void;
  onGroupCreated: (groupId: string) => void;
}

const CreateGroupModal: React.FC<Props> = ({ allUsers, onClose, onGroupCreated }) => {
  const { currentUser } = useAuth();
  const [groupName, setGroupName] = useState("");
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  const toggleUser = (uid: string) => {
    setSelectedUsers((prev) =>
      prev.includes(uid) ? prev.filter((id) => id !== uid) : [...prev, uid]
    );
  };

  const filteredUsers = allUsers.filter(
    (u) =>
      u.displayName?.toLowerCase().includes(search.toLowerCase()) ||
      u.email?.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = async () => {
    if (!groupName.trim()) return toast.error("Enter a group name");
    if (selectedUsers.length < 1) return toast.error("Select at least 1 member");
    if (!currentUser) return;

    setLoading(true);
    try {
      const groupRef = push(ref(database, "groups"));
      const groupId = groupRef.key!;

      const members: Record<string, boolean> = {
        [currentUser.uid]: true,
      };
      selectedUsers.forEach((uid) => {
        members[uid] = true;
      });

      await set(ref(database, `groups/${groupId}`), {
        name: groupName.trim(),
        createdBy: currentUser.uid,
        createdAt: serverTimestamp(),
        members,
        admins: { [currentUser.uid]: true },
        photoURL: "",
        description: "",
      });

      toast.success(`Group "${groupName}" created! 🎉`);
      onGroupCreated(groupId);
    } catch (err) {
      toast.error("Failed to create group");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-400" />
            <h2 className="text-white font-bold text-lg">Create Group</h2>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-xl transition-colors">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <div className="p-6 space-y-4 flex-1 overflow-y-auto">
          {/* Group Name */}
          <div>
            <label className="text-gray-400 text-xs font-medium mb-1.5 flex items-center gap-1.5">
              <Hash className="w-3.5 h-3.5" /> Group Name
            </label>
            <input
              type="text"
              placeholder="e.g. Project Team, Friends..."
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm transition-colors"
            />
          </div>

          {/* Selected Members Preview */}
          {selectedUsers.length > 0 && (
            <div>
              <p className="text-gray-400 text-xs font-medium mb-2">
                Selected ({selectedUsers.length})
              </p>
              <div className="flex flex-wrap gap-2">
                {selectedUsers.map((uid) => {
                  const user = allUsers.find((u) => u.uid === uid);
                  if (!user) return null;
                  return (
                    <div
                      key={uid}
                      onClick={() => toggleUser(uid)}
                      className="flex items-center gap-1.5 bg-indigo-600/30 border border-indigo-500/40 rounded-full px-3 py-1 cursor-pointer hover:bg-red-500/20 hover:border-red-500/40 transition-all group"
                    >
                      <img src={user.photoURL || `https://api.dicebear.com/7.x/initials/svg?seed=${user.displayName}`} alt="" className="w-5 h-5 rounded-full" />
                      <span className="text-indigo-300 group-hover:text-red-300 text-xs font-medium transition-colors">{user.displayName}</span>
                      <X className="w-3 h-3 text-indigo-400 group-hover:text-red-400 transition-colors" />
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Search Users */}
          <div>
            <label className="text-gray-400 text-xs font-medium mb-1.5 block">Add Members</label>
            <div className="relative mb-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search users..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm transition-colors"
              />
            </div>
            <div className="space-y-1 max-h-52 overflow-y-auto">
              {filteredUsers.map((user) => (
                <div
                  key={user.uid}
                  onClick={() => toggleUser(user.uid)}
                  className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all ${
                    selectedUsers.includes(user.uid)
                      ? "bg-indigo-600/20 border border-indigo-500/30"
                      : "hover:bg-gray-800 border border-transparent"
                  }`}
                >
                  <div className="relative">
                    <img
                      src={user.photoURL || `https://api.dicebear.com/7.x/initials/svg?seed=${user.displayName}`}
                      alt={user.displayName}
                      className="w-10 h-10 rounded-full border-2 border-gray-700"
                    />
                    <span className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-gray-900 ${user.online ? "bg-green-500" : "bg-gray-500"}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">{user.displayName}</p>
                    <p className="text-gray-500 text-xs truncate">{user.email}</p>
                  </div>
                  <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                    selectedUsers.includes(user.uid)
                      ? "bg-indigo-600 border-indigo-600"
                      : "border-gray-600"
                  }`}>
                    {selectedUsers.includes(user.uid) && <Check className="w-3.5 h-3.5 text-white" />}
                  </div>
                </div>
              ))}
              {filteredUsers.length === 0 && (
                <p className="text-gray-500 text-sm text-center py-4">No users found</p>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-800">
          <button
            onClick={handleCreate}
            disabled={loading || !groupName.trim() || selectedUsers.length < 1}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            <Users className="w-4 h-4" />
            {loading ? "Creating..." : `Create Group (${selectedUsers.length + 1} members)`}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateGroupModal;
