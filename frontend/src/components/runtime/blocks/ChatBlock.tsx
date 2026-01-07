"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
   Send,
   Paperclip,
   Smile,
   MoreHorizontal,
   Reply,
   Edit,
   Trash2,
   Heart,
   ThumbsUp,
   Check,
   CheckCheck,
} from "lucide-react";
import { BlockComponentProps } from "./index";
import { ChatProps } from "@/types/blueprint";

interface ChatMessage {
   id: string;
   [key: string]: any;
}

export function ChatBlock({
   block,
   data,
   loading,
   onCreate,
   onAction,
   context,
}: BlockComponentProps) {
   const props = block.props as ChatProps;
   const [message, setMessage] = useState("");
   const [replyTo, setReplyTo] = useState<ChatMessage | null>(null);
   const messagesEndRef = useRef<HTMLDivElement>(null);

   // Group messages by date
   const groupedMessages = useMemo(() => {
      if (!data || data.length === 0) return new Map();

      const groups = new Map<string, ChatMessage[]>();

      const sortedData = [...data].sort((a, b) => {
         const dateA = new Date(a[props.timestampField]);
         const dateB = new Date(b[props.timestampField]);
         return dateA.getTime() - dateB.getTime();
      });

      sortedData.forEach((msg) => {
         const date = new Date(msg[props.timestampField]);
         const dateKey = date.toLocaleDateString("en-US", {
            weekday: "long",
            month: "short",
            day: "numeric",
         });

         if (!groups.has(dateKey)) {
            groups.set(dateKey, []);
         }
         groups.get(dateKey)!.push(msg);
      });

      return groups;
   }, [data, props.timestampField]);

   // Scroll to bottom on new messages
   useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
   }, [data]);

   const handleSend = async () => {
      if (!message.trim()) return;

      const newMessage: any = {
         [props.messageField]: message,
         reply_to_id: replyTo?.id,
      };

      await onCreate?.(newMessage);
      setMessage("");
      setReplyTo(null);
   };

   const handleKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
         e.preventDefault();
         handleSend();
      }
   };

   const handleReaction = (msg: ChatMessage, reaction: string) => {
      onAction?.("reaction", { message: msg, reaction });
   };

   const handleReply = (msg: ChatMessage) => {
      setReplyTo(msg);
   };

   const handleMessageClick = (msg: ChatMessage) => {
      onAction?.("messageClick", { message: msg }, { selectedRecord: msg });
   };

   const isCurrentUser = (msg: ChatMessage) => {
      // In a real app, compare with current user ID
      return msg.sender_id === context?.user?.id;
   };

   const formatTime = (timestamp: string) => {
      return new Date(timestamp).toLocaleTimeString([], {
         hour: "2-digit",
         minute: "2-digit",
      });
   };

   const getInitials = (name: string) => {
      return name
         .split(" ")
         .map((n) => n[0])
         .join("")
         .toUpperCase()
         .slice(0, 2);
   };

   if (loading) {
      return (
         <Card className="flex flex-col h-[500px]">
            <div className="flex-1 p-4 space-y-4">
               {[1, 2, 3, 4].map((i) => (
                  <div
                     key={i}
                     className={`flex gap-3 ${i % 2 === 0 ? "flex-row-reverse" : ""}`}
                  >
                     <div className="w-10 h-10 rounded-full bg-white/10 animate-pulse" />
                     <div className="space-y-2">
                        <div className="h-4 w-24 bg-white/10 rounded animate-pulse" />
                        <div className="h-16 w-48 bg-white/5 rounded animate-pulse" />
                     </div>
                  </div>
               ))}
            </div>
         </Card>
      );
   }

   return (
      <Card className="flex flex-col h-[500px]">
         {/* Messages area */}
         <div className="flex-1 overflow-y-auto p-4">
            {Array.from(groupedMessages.entries()).map(([dateKey, messages]) => (
               <div key={dateKey}>
                  {/* Date separator */}
                  <div className="flex items-center gap-3 my-4">
                     <div className="h-px flex-1 bg-white/10" />
                     <span className="text-xs text-white/40 px-2">{dateKey}</span>
                     <div className="h-px flex-1 bg-white/10" />
                  </div>

                  {/* Messages */}
                  <div className="space-y-4">
                     {messages.map((msg: any) => {
                        const isOwn = isCurrentUser(msg);
                        const senderName = msg[props.senderNameField] || "Unknown";
                        const avatar = props.senderAvatarField
                           ? msg[props.senderAvatarField]
                           : null;
                        const content = msg[props.messageField];
                        const time = formatTime(msg[props.timestampField]);

                        return (
                           <div
                              key={msg.id}
                              className={`flex gap-3 group ${
                                 isOwn ? "flex-row-reverse" : ""
                              }`}
                           >
                              {/* Avatar */}
                              {avatar ? (
                                 <img
                                    src={avatar}
                                    alt={senderName}
                                    className="w-10 h-10 rounded-full object-cover"
                                 />
                              ) : (
                                 <div
                                    className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium ${
                                       isOwn
                                          ? "bg-primary-500/20 text-primary-400"
                                          : "bg-white/10 text-white/60"
                                    }`}
                                 >
                                    {getInitials(senderName)}
                                 </div>
                              )}

                              {/* Message content */}
                              <div className={`max-w-[70%] ${isOwn ? "items-end" : ""}`}>
                                 {/* Sender name & time */}
                                 <div
                                    className={`flex items-center gap-2 mb-1 ${
                                       isOwn ? "flex-row-reverse" : ""
                                    }`}
                                 >
                                    <span className="text-sm font-medium text-white/80">
                                       {senderName}
                                    </span>
                                    <span className="text-xs text-white/40">{time}</span>
                                 </div>

                                 {/* Message bubble */}
                                 <div
                                    className={`relative rounded-2xl px-4 py-2.5 ${
                                       isOwn
                                          ? "bg-primary-500 text-white rounded-br-sm"
                                          : "bg-white/10 text-white/90 rounded-bl-sm"
                                    }`}
                                    onClick={() => handleMessageClick(msg)}
                                 >
                                    {/* Reply reference */}
                                    {msg.reply_to_id && (
                                       <div
                                          className={`text-xs mb-2 pb-2 border-b ${
                                             isOwn
                                                ? "border-white/20 text-white/70"
                                                : "border-white/10 text-white/50"
                                          }`}
                                       >
                                          <Reply className="w-3 h-3 inline mr-1" />
                                          Replying to a message
                                       </div>
                                    )}

                                    <p className="whitespace-pre-wrap">{content}</p>

                                    {/* Read status for own messages */}
                                    {isOwn && (
                                       <div className="flex justify-end mt-1">
                                          <CheckCheck className="w-4 h-4 text-white/60" />
                                       </div>
                                    )}
                                 </div>

                                 {/* Actions */}
                                 <div
                                    className={`flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity ${
                                       isOwn ? "flex-row-reverse" : ""
                                    }`}
                                 >
                                    {props.allowReactions && (
                                       <>
                                          <button
                                             className="p-1 rounded hover:bg-white/10 text-white/40 hover:text-white transition-colors"
                                             onClick={() => handleReaction(msg, "like")}
                                          >
                                             <ThumbsUp className="w-3.5 h-3.5" />
                                          </button>
                                          <button
                                             className="p-1 rounded hover:bg-white/10 text-white/40 hover:text-white transition-colors"
                                             onClick={() => handleReaction(msg, "heart")}
                                          >
                                             <Heart className="w-3.5 h-3.5" />
                                          </button>
                                       </>
                                    )}
                                    {props.allowReply && (
                                       <button
                                          className="p-1 rounded hover:bg-white/10 text-white/40 hover:text-white transition-colors"
                                          onClick={() => handleReply(msg)}
                                       >
                                          <Reply className="w-3.5 h-3.5" />
                                       </button>
                                    )}
                                    {isOwn && props.allowEdit && (
                                       <button className="p-1 rounded hover:bg-white/10 text-white/40 hover:text-white transition-colors">
                                          <Edit className="w-3.5 h-3.5" />
                                       </button>
                                    )}
                                    {isOwn && props.allowDelete && (
                                       <button className="p-1 rounded hover:bg-white/10 text-red-400 hover:text-red-300 transition-colors">
                                          <Trash2 className="w-3.5 h-3.5" />
                                       </button>
                                    )}
                                 </div>
                              </div>
                           </div>
                        );
                     })}
                  </div>
               </div>
            ))}

            {/* Empty state */}
            {(!data || data.length === 0) && (
               <div className="flex flex-col items-center justify-center h-full text-white/40">
                  <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
                     <Send className="w-8 h-8" />
                  </div>
                  <p>No messages yet</p>
                  <p className="text-sm">Start the conversation!</p>
               </div>
            )}

            <div ref={messagesEndRef} />
         </div>

         {/* Reply indicator */}
         {replyTo && (
            <div className="px-4 py-2 bg-white/5 border-t border-white/10 flex items-center justify-between">
               <div className="flex items-center gap-2 text-sm text-white/60">
                  <Reply className="w-4 h-4" />
                  <span>
                     Replying to <strong>{replyTo[props.senderNameField]}</strong>
                  </span>
               </div>
               <button
                  className="text-white/40 hover:text-white"
                  onClick={() => setReplyTo(null)}
               >
                  ×
               </button>
            </div>
         )}

         {/* Input area */}
         <div className="p-4 border-t border-white/10">
            <div className="flex items-end gap-3">
               {props.allowAttachments && (
                  <Button variant="ghost" size="sm" className="text-white/40">
                     <Paperclip className="w-5 h-5" />
                  </Button>
               )}

               <div className="flex-1 relative">
                  <Textarea
                     value={message}
                     onChange={(e) => setMessage(e.target.value)}
                     onKeyDown={handleKeyDown}
                     placeholder="Type a message..."
                     className="min-h-[44px] max-h-32 resize-none pr-10"
                     rows={1}
                  />
                  <button className="absolute right-3 bottom-2.5 text-white/40 hover:text-white transition-colors">
                     <Smile className="w-5 h-5" />
                  </button>
               </div>

               <Button
                  onClick={handleSend}
                  disabled={!message.trim()}
                  className="h-11"
               >
                  <Send className="w-5 h-5" />
               </Button>
            </div>
         </div>
      </Card>
   );
}

