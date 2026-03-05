import React, { useEffect, useRef, useState } from "react";
import {
  ref, onValue, push, get, update, remove
} from "firebase/database";
import { database } from "../firebase/config";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";
import {
  Send, ArrowLeft,
  Smile, Trash2, Reply, Copy,
  Info, UserMinus, UserPlus, X, Hash
} from "lucide-react";
import { formatDistanceToNow, format, isToday, isYesterday } from "date-fns";

interface Message {
  id: string;
  text: string;
  senderId: string;
  senderName: string;
  senderPhoto: string;
  timestamp: number;
  type: "text" | "emoji";
  replyTo?: { id: string; text: string; senderName: string };
}

interface GroupInfo {
  name: string;
  members: Record<string, boolean>;
  admins: Record<string, boolean>;
  createdBy: string;
  description: string;
}

interface UserInfo {
  displayName: string;
  email: string;
  photoURL: string;
  online: boolean;
  lastSeen: number;
  bio: string;
}

interface Props {
  chatId: string;
  chatType: "private" | "group";
  onOpenSidebar: () => void;
  sidebarOpen: boolean;
}

const EMOJIS = ["😀","😂","❤️","👍","🎉","🔥","😎","🙏","💯","😍","🤔","😭","😊","🥳","👏","💪","🤝","✅","⭐","🚀"];

const ChatWindow: React.FC<Props> = ({ chatId, chatType, onOpenSidebar, sidebarOpen }) => {
  const { currentUser } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [otherUser, setOtherUser] = useState<UserInfo | null>(null);
  const [groupInfo, setGroupInfo] = useState<GroupInfo | null>(null);
  const [groupMembers, setGroupMembers] = useState<UserInfo[]>([]);
  const [showInfo, setShowInfo] = useState(false);
  const [showEmojis, setShowEmojis] = useState(false);
  const [replyTo, setReplyTo] = useState<Message | null>(null);
  const [hoveredMsg, setHoveredMsg] = useState<string | null>(null);
  const [showAddMember, setShowAddMember] = useState(false);
  const [allUsers, setAllUsers] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const messagesPath = chatType === "group" ? `groupMessages/${chatId}` : `messages/${chatId}`;

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Fetch messages
  useEffect(() => {
    const msgsRef = ref(database, messagesPath);
    const unsub = onValue(msgsRef, (snap) => {
      const data = snap.val();
      if (!data) { setMessages([]); return; }
      const list = Object.entries(data).map(([id, msg]: any) => ({ id, ...msg }));
      list.sort((a: any, b: any) => a.timestamp - b.timestamp);
      setMessages(list as Message[]);
    });
    return () => unsub();
  }, [chatId, messagesPath]);

  // Fetch other user info (private chat)
  useEffect(() => {
    if (chatType !== "private") return;
    const fetchOtherUser = async () => {
      const chatSnap = await get(ref(database, `chats/${chatId}`));
      const chatData = chatSnap.val();
      if (!chatData?.members) return;
      const otherUid = chatData.members.find((m: string) => m !== currentUser?.uid);
      if (!otherUid) return;
      const userRef = ref(database, `users/${otherUid}`);
      onValue(userRef, (snap) => {
        setOtherUser(snap.val());
      });
    };
    fetchOtherUser();
  }, [chatId, chatType, currentUser]);

  // Fetch group info
  useEffect(() => {
    if (chatType !== "group") return;
    const groupRef = ref(database, `groups/${chatId}`);
    const unsub = onValue(groupRef, async (snap) => {
      const data = snap.val();
      if (!data) return;
      setGroupInfo(data);
      // Fetch member details
      if (data.members) {
        const memberList: any[] = [];
        for (const uid of Object.keys(data.members)) {
          const userSnap = await get(ref(database, `users/${uid}`));
          if (userSnap.val()) memberList.push({ uid, ...userSnap.val() });
        }
        setGroupMembers(memberList);
      }
    });
    return () => unsub();
  }, [chatId, chatType]);

  // Fetch all users (for add member)
  useEffect(() => {
    if (chatType !== "group") return;
    const usersRef = ref(database, "users");
    const unsub = onValue(usersRef, (snap) => {
      const data = snap.val();
      if (data) {
        setAllUsers(Object.values(data) as any[]);
      }
    });
    return () => unsub();
  }, [chatType]);

  const sendMessage = async () => {
    if (!text.trim() || !currentUser) return;
    const msgData: any = {
      text: text.trim(),
      senderId: currentUser.uid,
      senderName: currentUser.displayName || "User",
      senderPhoto: `https://api.dicebear.com/7.x/initials/svg?seed=${currentUser.displayName}`,
      timestamp: Date.now(),
      type: "text",
    };
    if (replyTo) {
      msgData.replyTo = {
        id: replyTo.id,
        text: replyTo.text,
        senderName: replyTo.senderName,
      };
    }
    try {
      await push(ref(database, messagesPath), msgData);
      setText("");
      setReplyTo(null);
      setShowEmojis(false);
      inputRef.current?.focus();
    } catch {
      toast.error("Failed to send message");
    }
  };

  const deleteMessage = async (msgId: string) => {
    try {
      await remove(ref(database, `${messagesPath}/${msgId}`));
      toast.success("Message deleted");
    } catch {
      toast.error("Failed to delete message");
    }
  };

  const addMemberToGroup = async (uid: string) => {
    if (!groupInfo || !currentUser) return;
    if (groupInfo.members[uid]) return toast.error("User already in group");
    if (!groupInfo.admins?.[currentUser.uid]) return toast.error("Only admins can add members");
    try {
      await update(ref(database, `groups/${chatId}/members`), { [uid]: true });
      toast.success("Member added!");
    } catch {
      toast.error("Failed to add member");
    }
  };

  const removeMember = async (uid: string) => {
    if (!groupInfo || !currentUser) return;
    if (!groupInfo.admins?.[currentUser.uid]) return toast.error("Only admins can remove members");
    if (uid === groupInfo.createdBy) return toast.error("Cannot remove group creator");
    try {
      await remove(ref(database, `groups/${chatId}/members/${uid}`));
      toast.success("Member removed");
    } catch {
      toast.error("Failed to remove member");
    }
  };

  const leaveGroup = async () => {
    if (!currentUser) return;
    try {
      await remove(ref(database, `groups/${chatId}/members/${currentUser.uid}`));
      toast.success("Left the group");
    } catch {
      toast.error("Failed to leave group");
    }
  };

  const copyMessage = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied!");
  };

  const formatMsgTime = (timestamp: number) => {
    if (!timestamp) return "";
    return format(new Date(timestamp), "HH:mm");
  };

  const getDateLabel = (timestamp: number) => {
    const date = new Date(timestamp);
    if (isToday(date)) return "Today";
    if (isYesterday(date)) return "Yesterday";
    return format(date, "MMMM d, yyyy");
  };

  // Group messages by date
  const groupedMessages: { date: string; messages: Message[] }[] = [];
  messages.forEach((msg) => {
    const dateLabel = getDateLabel(msg.timestamp);
    const last = groupedMessages[groupedMessages.length - 1];
    if (last && last.date === dateLabel) {
      last.messages.push(msg);
    } else {
      groupedMessages.push({ date: dateLabel, messages: [msg] });
    }
  });

  const headerName = chatType === "group" ? groupInfo?.name : otherUser?.displayName;
  const headerSub = chatType === "group"
    ? `${Object.keys(groupInfo?.members || {}).length} members`
    : otherUser?.online ? "Online" : otherUser?.lastSeen
    ? `Last seen ${formatDistanceToNow(new Date(otherUser.lastSeen), { addSuffix: true })}`
    : "Offline";

  const nonMembers = allUsers.filter(
    (u) => u.uid !== currentUser?.uid && !groupInfo?.members?.[u.uid]
  );

  return (
    <div className="flex h-full">
      {/* Main Chat */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 bg-gray-900 border-b border-gray-800 shadow-sm flex-shrink-0">
          {!sidebarOpen && (
            <button onClick={onOpenSidebar} className="p-2 hover:bg-gray-800 rounded-xl text-gray-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div className="flex items-center gap-3 flex-1 cursor-pointer" onClick={() => setShowInfo(!showInfo)}>
            {chatType === "group" ? (
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center border-2 border-gray-700">
                <Hash className="w-5 h-5 text-white" />
              </div>
            ) : (
              <div className="relative">
                <img
                  src={`https://api.dicebear.com/7.x/initials/svg?seed=${headerName}`}
                  alt=""
                  className="w-10 h-10 rounded-full border-2 border-gray-700"
                />
                {chatType === "private" && (
                  <span className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-gray-900 ${otherUser?.online ? "bg-green-500" : "bg-gray-500"}`} />
                )}
              </div>
            )}
            <div>
              <p className="text-white font-semibold text-sm">{headerName || "Loading..."}</p>
              <p className={`text-xs ${otherUser?.online && chatType === "private" ? "text-green-400" : "text-gray-500"}`}>
                {headerSub}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {chatType === "group" && (
              <button
                onClick={() => setShowInfo(!showInfo)}
                className="p-2 hover:bg-gray-800 rounded-xl text-gray-400 hover:text-indigo-400 transition-colors"
              >
                <Info className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Messages Area */}
        <div
          className="flex-1 overflow-y-auto p-4 space-y-1"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(99,102,241,0.05) 1px, transparent 0)`,
            backgroundSize: "32px 32px",
            backgroundColor: "#111827"
          }}
          onClick={() => { setShowEmojis(false); setHoveredMsg(null); }}
        >
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mb-4">
                <Smile className="w-8 h-8 text-gray-600" />
              </div>
              <p className="text-gray-500 text-sm">No messages yet</p>
              <p className="text-gray-600 text-xs mt-1">Say hello! 👋</p>
            </div>
          )}

          {groupedMessages.map(({ date, messages: dayMsgs }) => (
            <div key={date}>
              {/* Date label */}
              <div className="flex items-center gap-3 my-4">
                <div className="flex-1 h-px bg-gray-800" />
                <span className="text-gray-500 text-xs bg-gray-800 px-3 py-1 rounded-full">{date}</span>
                <div className="flex-1 h-px bg-gray-800" />
              </div>

              {dayMsgs.map((msg, idx) => {
                const isMe = msg.senderId === currentUser?.uid;
                const showAvatar = !isMe && (idx === 0 || dayMsgs[idx - 1]?.senderId !== msg.senderId);
                const showName = chatType === "group" && !isMe && showAvatar;

                return (
                  <div
                    key={msg.id}
                    className={`flex items-end gap-2 mb-1 group ${isMe ? "flex-row-reverse" : "flex-row"}`}
                    onMouseEnter={() => setHoveredMsg(msg.id)}
                    onMouseLeave={() => setHoveredMsg(null)}
                  >
                    {/* Avatar */}
                    {!isMe && (
                      <div className="w-8 flex-shrink-0">
                        {showAvatar && (
                          <img
                            src={msg.senderPhoto || `https://api.dicebear.com/7.x/initials/svg?seed=${msg.senderName}`}
                            alt=""
                            className="w-8 h-8 rounded-full border border-gray-700"
                          />
                        )}
                      </div>
                    )}

                    <div className={`max-w-[70%] ${isMe ? "items-end" : "items-start"} flex flex-col`}>
                      {showName && (
                        <span className="text-xs text-indigo-400 font-medium mb-1 ml-1">{msg.senderName}</span>
                      )}

                      {/* Reply preview */}
                      {msg.replyTo && (
                        <div className={`px-3 py-1.5 rounded-t-xl border-l-2 border-indigo-400 bg-gray-800/80 text-xs text-gray-400 mb-0.5 max-w-full ${isMe ? "bg-indigo-900/30" : ""}`}>
                          <span className="text-indigo-400 font-medium">{msg.replyTo.senderName}</span>
                          <p className="truncate">{msg.replyTo.text}</p>
                        </div>
                      )}

                      {/* Message bubble */}
                      <div className={`relative px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm ${
                        isMe
                          ? "bg-indigo-600 text-white rounded-br-sm"
                          : "bg-gray-800 text-gray-100 rounded-bl-sm"
                      } ${msg.replyTo ? "rounded-t-sm" : ""}`}>
                        <p className="break-words">{msg.text}</p>
                        <p className={`text-xs mt-1 ${isMe ? "text-indigo-200" : "text-gray-500"}`}>
                          {formatMsgTime(msg.timestamp)}
                        </p>
                      </div>
                    </div>

                    {/* Message actions */}
                    {hoveredMsg === msg.id && (
                      <div className={`flex items-center gap-1 ${isMe ? "flex-row-reverse" : "flex-row"}`}>
                        <button
                          onClick={(e) => { e.stopPropagation(); setReplyTo(msg); inputRef.current?.focus(); }}
                          className="p-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors"
                          title="Reply"
                        >
                          <Reply className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); copyMessage(msg.text); }}
                          className="p-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors"
                          title="Copy"
                        >
                          <Copy className="w-3.5 h-3.5" />
                        </button>
                        {isMe && (
                          <button
                            onClick={(e) => { e.stopPropagation(); deleteMessage(msg.id); }}
                            className="p-1.5 bg-gray-800 hover:bg-red-600 rounded-lg text-gray-400 hover:text-white transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Reply Preview */}
        {replyTo && (
          <div className="flex items-center gap-3 px-4 py-2.5 bg-gray-800 border-t border-gray-700">
            <div className="flex-1 border-l-2 border-indigo-400 pl-3">
              <p className="text-indigo-400 text-xs font-medium">Replying to {replyTo.senderName}</p>
              <p className="text-gray-400 text-xs truncate">{replyTo.text}</p>
            </div>
            <button onClick={() => setReplyTo(null)} className="text-gray-500 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Emoji Picker */}
        {showEmojis && (
          <div className="px-4 py-3 bg-gray-900 border-t border-gray-800 flex flex-wrap gap-2">
            {EMOJIS.map((emoji) => (
              <button
                key={emoji}
                onClick={() => { setText((prev) => prev + emoji); inputRef.current?.focus(); }}
                className="text-2xl hover:scale-125 transition-transform"
              >
                {emoji}
              </button>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div className="flex items-center gap-2 px-4 py-3 bg-gray-900 border-t border-gray-800 flex-shrink-0">
          <button
            onClick={(e) => { e.stopPropagation(); setShowEmojis(!showEmojis); }}
            className={`p-2.5 rounded-xl transition-colors flex-shrink-0 ${showEmojis ? "bg-indigo-600 text-white" : "text-gray-500 hover:text-indigo-400 hover:bg-gray-800"}`}
          >
            <Smile className="w-5 h-5" />
          </button>
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a message..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
            className="flex-1 px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm transition-colors"
          />
          <button
            onClick={sendMessage}
            disabled={!text.trim()}
            className="p-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl transition-colors flex-shrink-0 shadow-lg"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Group Info Panel */}
      {showInfo && chatType === "group" && groupInfo && (
        <div className="w-72 bg-gray-900 border-l border-gray-800 flex flex-col overflow-hidden flex-shrink-0">
          <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <h3 className="text-white font-semibold">Group Info</h3>
            <button onClick={() => setShowInfo(false)} className="p-1 hover:bg-gray-800 rounded-lg text-gray-400">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            {/* Group avatar & name */}
            <div className="p-6 text-center border-b border-gray-800">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto mb-3 border-4 border-gray-800">
                <Hash className="w-10 h-10 text-white" />
              </div>
              <h4 className="text-white font-bold text-lg">{groupInfo.name}</h4>
              <p className="text-gray-500 text-sm mt-1">
                {Object.keys(groupInfo.members).length} members
              </p>
              {groupInfo.description && (
                <p className="text-gray-400 text-sm mt-2">{groupInfo.description}</p>
              )}
            </div>

            {/* Members */}
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <p className="text-gray-400 text-xs font-semibold uppercase tracking-wide">Members</p>
                {groupInfo.admins?.[currentUser?.uid || ""] && (
                  <button
                    onClick={() => setShowAddMember(!showAddMember)}
                    className="p-1.5 bg-indigo-600/20 hover:bg-indigo-600/40 rounded-lg text-indigo-400 transition-colors"
                  >
                    <UserPlus className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Add member dropdown */}
              {showAddMember && nonMembers.length > 0 && (
                <div className="mb-3 bg-gray-800 rounded-xl p-2 space-y-1">
                  <p className="text-gray-500 text-xs px-2 mb-2">Add members:</p>
                  {nonMembers.map((u: any) => (
                    <button
                      key={u.uid}
                      onClick={() => addMemberToGroup(u.uid)}
                      className="w-full flex items-center gap-2 p-2 hover:bg-gray-700 rounded-lg transition-colors"
                    >
                      <img src={u.photoURL || `https://api.dicebear.com/7.x/initials/svg?seed=${u.displayName}`} alt="" className="w-7 h-7 rounded-full" />
                      <span className="text-white text-xs font-medium flex-1 text-left truncate">{u.displayName}</span>
                      <UserPlus className="w-3.5 h-3.5 text-indigo-400" />
                    </button>
                  ))}
                </div>
              )}

              <div className="space-y-2">
                {groupMembers.map((member: any) => (
                  <div key={member.uid} className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-800 transition-colors">
                    <div className="relative">
                      <img
                        src={member.photoURL || `https://api.dicebear.com/7.x/initials/svg?seed=${member.displayName}`}
                        alt=""
                        className="w-9 h-9 rounded-full border border-gray-700"
                      />
                      <span className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-gray-900 ${member.online ? "bg-green-500" : "bg-gray-500"}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm font-medium truncate">
                        {member.displayName}
                        {member.uid === currentUser?.uid && <span className="text-gray-500 text-xs ml-1">(You)</span>}
                      </p>
                      {groupInfo.admins?.[member.uid] && (
                        <span className="text-indigo-400 text-xs">Admin</span>
                      )}
                    </div>
                    {groupInfo.admins?.[currentUser?.uid || ""] && member.uid !== currentUser?.uid && member.uid !== groupInfo.createdBy && (
                      <button
                        onClick={() => removeMember(member.uid)}
                        className="p-1 hover:bg-red-500/20 rounded-lg text-gray-600 hover:text-red-400 transition-colors"
                      >
                        <UserMinus className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Leave Group */}
            <div className="p-4 border-t border-gray-800">
              <button
                onClick={leaveGroup}
                className="w-full py-2.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-400 hover:text-red-300 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
              >
                <UserMinus className="w-4 h-4" />
                Leave Group
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatWindow;
