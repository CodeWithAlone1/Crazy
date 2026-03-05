import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";
import { MessageCircle } from "lucide-react";

export type ChatType = { id: string; type: "private" | "group" };

const ChatPage: React.FC = () => {
  const [activeChat, setActiveChat] = useState<ChatType | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="h-screen bg-gray-950 flex overflow-hidden">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? "w-80 min-w-[320px]" : "w-0"} transition-all duration-300 flex-shrink-0 overflow-hidden`}>
        <Sidebar
          activeChat={activeChat}
          setActiveChat={(chat) => {
            setActiveChat(chat);
            if (window.innerWidth < 768) setSidebarOpen(false);
          }}
          onCloseSidebar={() => setSidebarOpen(false)}
        />
      </div>

      {/* Chat Window */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {activeChat ? (
          <ChatWindow
            chatId={activeChat.id}
            chatType={activeChat.type}
            onOpenSidebar={() => setSidebarOpen(true)}
            sidebarOpen={sidebarOpen}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center bg-gray-900">
            <div className="text-center">
              <div className="w-24 h-24 bg-indigo-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <MessageCircle className="w-12 h-12 text-indigo-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Welcome to FireChat</h2>
              <p className="text-gray-400 max-w-sm">
                Select a conversation from the sidebar or search for users to start chatting
              </p>
              {!sidebarOpen && (
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="mt-6 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-semibold transition-colors"
                >
                  Open Sidebar
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatPage;
