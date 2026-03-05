import React, { useEffect, useState } from "react";
import { ref, onValue, push, set, serverTimestamp, get } from "firebase/database";
import { database } from "../firebase/config";
import { useAuth } from "../context/AuthContext";
import { ChatType } from "../pages/ChatPage";
import toast from "react-hot-toast";
import {
  Search, Users, MessageCircle, Plus, X, LogOut,
  UserPlus, ChevronDown, Settings, Hash
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import UserProfileModal from "./UserProfileModal";
import CreateGroupModal from "./CreateGroupModal";

interface SidebarProps {
  activeChat: ChatType | null;
  setActiveChat: (chat: ChatType) => void;
  onCloseSidebar: () => void;
}

interface UserData {
  uid: string;
  displayName: string;
  email: string;
  photoURL: string;
  online: boolean;
  lastSeen: number;
  bio: string;
}

interface ChatPreview {
  id: string;
  type: "private" | "group";
  name: string;
  photoURL: string;
  lastMessage: string;
  lastMessageTime: number;
  unread: number;
  online?: boolean;
  membersCount?: number;
}

const Sidebar: React.FC<SidebarProps> = ({ activeChat, setActiveChat, onCloseSidebar }) => {
  const { currentUser, logout } = useAuth();
  const [tab, setTab] = useState<"chats" | "groups" | "users">("chats");
  const [searchQuery, setSearchQuery] = useState("");
  const [allUsers, setAllUsers] = useState<UserData[]>([]);
  const [chats, setChats] = useState<ChatPreview[]>([]);
  const [groups, setGroups] = useState<ChatPreview[]>([]);
  const [showProfile, setShowProfile] = useState(false);
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Fetch all users
  useEffect(() => {
    const usersRef = ref(database, "users");
    const unsub = onValue(usersRef, (snap) => {
      const data = snap.val();
      if (data) {
        const list = Object.values(data) as UserData[];
        setAllUsers(list.filter((u) => u.uid !== currentUser?.uid));
      }
    });
    return () => unsub();
  }, [currentUser]);

  // Fetch private chats
  useEffect(() => {
    if (!currentUser) return;
    const chatsRef = ref(database, `userChats/${currentUser.uid}`);
    const unsub = onValue(chatsRef, async (snap) => {
      const data = snap.val();
      if (!data) { setChats([]); return; }
      const chatList: ChatPreview[] = [];
      for (const chatId of Object.keys(data)) {
        const chatSnap = await get(ref(database, `chats/${chatId}`));
        const chatData = chatSnap.val();
        if (!chatData) continue;
        const otherUid = chatData.members?.find((m: string) => m !== currentUser.uid);
        const userSnap = await get(ref(database, `users/${otherUid}`));
        const userData = userSnap.val();
        if (!userData) continue;
        // Last message
        const msgsSnap = await get(ref(database, `messages/${chatId}`));
        const msgs = msgsSnap.val();
        let lastMessage = "No messages yet";
        let lastMessageTime = chatData.createdAt || 0;
        if (msgs) {
          const msgList = Object.values(msgs) as any[];
          const last = msgList[msgList.length - 1];
          lastMessage = last.type === "image" ? "📷 Photo" : last.text;
          lastMessageTime = last.timestamp;
        }
        chatList.push({
          id: chatId,
          type: "private",
          name: userData.displayName,
          photoURL: userData.photoURL,
          lastMessage,
          lastMessageTime,
          unread: 0,
          online: userData.online,
        });
      }
      chatList.sort((a, b) => b.lastMessageTime - a.lastMessageTime);
      setChats(chatList);
    });
    return () => unsub();
  }, [currentUser]);

  // Fetch groups
  useEffect(() => {
    if (!currentUser) return;
    const groupsRef = ref(database, "groups");
    const unsub = onValue(groupsRef, async (snap) => {
      const data = snap.val();
      if (!data) { setGroups([]); return; }
      const groupList: ChatPreview[] = [];
      for (const [groupId, group] of Object.entries(data) as any) {
        if (!group.members || !group.members[currentUser.uid]) continue;
        const msgsSnap = await get(ref(database, `groupMessages/${groupId}`));
        const msgs = msgsSnap.val();
        let lastMessage = "No messages yet";
        let lastMessageTime = group.createdAt || 0;
        if (msgs) {
          const msgList = Object.values(msgs) as any[];
          const last = msgList[msgList.length - 1];
          lastMessage = last.type === "image" ? "📷 Photo" : `${last.senderName}: ${last.text}`;
          lastMessageTime = last.timestamp;
        }
        groupList.push({
          id: groupId,
          type: "group",
          name: group.name,
          photoURL: group.photoURL || "",
          lastMessage,
          lastMessageTime,
          unread: 0,
          membersCount: Object.keys(group.members).length,
        });
      }
      groupList.sort((a, b) => b.lastMessageTime - a.lastMessageTime);
      setGroups(groupList);
    });
    return () => unsub();
  }, [currentUser]);

  const startPrivateChat = async (user: UserData) => {
    if (!currentUser) return;
    // Check if chat already exists
    const userChatsSnap = await get(ref(database, `userChats/${currentUser.uid}`));
    const userChats = userChatsSnap.val() || {};
    for (const chatId of Object.keys(userChats)) {
      const chatSnap = await get(ref(database, `chats/${chatId}`));
      const chatData = chatSnap.val();
      if (chatData?.members?.includes(user.uid)) {
        setActiveChat({ id: chatId, type: "private" });
        setTab("chats");
        return;
      }
    }
    // Create new chat
    const chatRef = push(ref(database, "chats"));
    const chatId = chatRef.key!;
    await set(ref(database, `chats/${chatId}`), {
      members: [currentUser.uid, user.uid],
      createdAt: serverTimestamp(),
    });
    await set(ref(database, `userChats/${currentUser.uid}/${chatId}`), true);
    await set(ref(database, `userChats/${user.uid}/${chatId}`), true);
    setActiveChat({ id: chatId, type: "private" });
    setTab("chats");
    toast.success(`Chat started with ${user.displayName}`);
  };

  const filteredUsers = allUsers.filter(
    (u) =>
      u.displayName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredChats = chats.filter((c) =>
    c.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredGroups = groups.filter((g) =>
    g.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleLogout = async () => {
    try {
      await logout();
      toast.success("Logged out successfully");
    } catch {
      toast.error("Failed to logout");
    }
  };

  return (
    <div className="h-full bg-gray-900 flex flex-col border-r border-gray-800">
      {/* Header */}
      <div className="p-4 border-b border-gray-800 bg-gray-900">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <MessageCircle className="w-6 h-6 text-indigo-400" />
            <span className="text-white font-bold text-lg">FireChat</span>
          </div>
          <div className="flex items-center gap-1">
            {tab === "groups" && (
              <button
                onClick={() => setShowCreateGroup(true)}
                className="p-2 text-gray-400 hover:text-indigo-400 hover:bg-gray-800 rounded-xl transition-all"
                title="Create Group"
              >
                <Plus className="w-5 h-5" />
              </button>
            )}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 p-1.5 rounded-xl hover:bg-gray-800 transition-all"
              >
                <img
                  src={`https://api.dicebear.com/7.x/initials/svg?seed=${currentUser?.displayName}`}
                  alt=""
                  className="w-8 h-8 rounded-full border-2 border-indigo-500"
                />
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </button>
              {showUserMenu && (
                <div className="absolute right-0 top-12 bg-gray-800 border border-gray-700 rounded-xl shadow-2xl py-1 z-50 w-44">
                  <button
                    onClick={() => { setShowProfile(true); setShowUserMenu(false); }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors text-sm"
                  >
                    <Settings className="w-4 h-4" /> My Profile
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-red-400 hover:bg-gray-700 hover:text-red-300 transition-colors text-sm"
                  >
                    <LogOut className="w-4 h-4" /> Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm transition-colors"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2">
              <X className="w-4 h-4 text-gray-500 hover:text-white" />
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-800">
        {[
          { key: "chats", label: "Chats", icon: MessageCircle },
          { key: "groups", label: "Groups", icon: Hash },
          { key: "users", label: "Find Users", icon: UserPlus },
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key as any)}
            className={`flex-1 flex flex-col items-center py-3 gap-0.5 text-xs font-medium transition-all border-b-2 ${
              tab === key
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-gray-500 hover:text-gray-300"
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {/* Chats Tab */}
        {tab === "chats" && (
          <div>
            {filteredChats.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
                <MessageCircle className="w-12 h-12 text-gray-700 mb-3" />
                <p className="text-gray-500 text-sm">No chats yet</p>
                <p className="text-gray-600 text-xs mt-1">Find users to start chatting</p>
              </div>
            ) : (
              filteredChats.map((chat) => (
                <ChatItem
                  key={chat.id}
                  chat={chat}
                  isActive={activeChat?.id === chat.id}
                  onClick={() => setActiveChat({ id: chat.id, type: "private" })}
                />
              ))
            )}
          </div>
        )}

        {/* Groups Tab */}
        {tab === "groups" && (
          <div>
            <div className="p-3">
              <button
                onClick={() => setShowCreateGroup(true)}
                className="w-full flex items-center gap-3 p-3 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 rounded-xl text-indigo-400 text-sm font-medium transition-all"
              >
                <Plus className="w-5 h-5" />
                Create New Group
              </button>
            </div>
            {filteredGroups.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                <Users className="w-12 h-12 text-gray-700 mb-3" />
                <p className="text-gray-500 text-sm">No groups yet</p>
                <p className="text-gray-600 text-xs mt-1">Create a group to chat with multiple people</p>
              </div>
            ) : (
              filteredGroups.map((group) => (
                <ChatItem
                  key={group.id}
                  chat={group}
                  isActive={activeChat?.id === group.id}
                  onClick={() => setActiveChat({ id: group.id, type: "group" })}
                />
              ))
            )}
          </div>
        )}

        {/* Find Users Tab */}
        {tab === "users" && (
          <div>
            {filteredUsers.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
                <Users className="w-12 h-12 text-gray-700 mb-3" />
                <p className="text-gray-500 text-sm">
                  {searchQuery ? "No users found" : "No other users yet"}
                </p>
              </div>
            ) : (
              filteredUsers.map((user) => (
                <div
                  key={user.uid}
                  onClick={() => startPrivateChat(user)}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-gray-800 cursor-pointer transition-colors border-b border-gray-800/50"
                >
                  <div className="relative flex-shrink-0">
                    <img
                      src={user.photoURL || `https://api.dicebear.com/7.x/initials/svg?seed=${user.displayName}`}
                      alt={user.displayName}
                      className="w-12 h-12 rounded-full border-2 border-gray-700"
                    />
                    <span className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-gray-900 ${user.online ? "bg-green-500" : "bg-gray-500"}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium text-sm truncate">{user.displayName}</p>
                    <p className="text-gray-500 text-xs truncate">{user.email}</p>
                    <p className="text-gray-600 text-xs truncate">{user.bio}</p>
                  </div>
                  <button className="p-2 bg-indigo-600/20 hover:bg-indigo-600/40 rounded-lg text-indigo-400 transition-colors flex-shrink-0">
                    <MessageCircle className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* User Profile Modal */}
      {showProfile && (
        <UserProfileModal onClose={() => setShowProfile(false)} />
      )}

      {/* Create Group Modal */}
      {showCreateGroup && (
        <CreateGroupModal
          allUsers={allUsers}
          onClose={() => setShowCreateGroup(false)}
          onGroupCreated={(groupId) => {
            setActiveChat({ id: groupId, type: "group" });
            setTab("groups");
            setShowCreateGroup(false);
          }}
        />
      )}
    </div>
  );
};

const ChatItem: React.FC<{
  chat: ChatPreview;
  isActive: boolean;
  onClick: () => void;
}> = ({ chat, isActive, onClick }) => {
  return (
    <div
      onClick={onClick}
      className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-all border-b border-gray-800/50 ${
        isActive ? "bg-indigo-600/20 border-l-2 border-l-indigo-500" : "hover:bg-gray-800"
      }`}
    >
      <div className="relative flex-shrink-0">
        {chat.type === "group" ? (
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center border-2 border-gray-700">
            <Hash className="w-6 h-6 text-white" />
          </div>
        ) : (
          <img
            src={chat.photoURL || `https://api.dicebear.com/7.x/initials/svg?seed=${chat.name}`}
            alt={chat.name}
            className="w-12 h-12 rounded-full border-2 border-gray-700"
          />
        )}
        {chat.type === "private" && (
          <span className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-gray-900 ${chat.online ? "bg-green-500" : "bg-gray-500"}`} />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <p className="text-white font-medium text-sm truncate">{chat.name}</p>
          {chat.lastMessageTime > 0 && (
            <span className="text-gray-500 text-xs flex-shrink-0 ml-1">
              {formatDistanceToNow(new Date(chat.lastMessageTime), { addSuffix: false })}
            </span>
          )}
        </div>
        <p className="text-gray-500 text-xs truncate mt-0.5">{chat.lastMessage}</p>
        {chat.type === "group" && (
          <p className="text-gray-600 text-xs">{chat.membersCount} members</p>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
