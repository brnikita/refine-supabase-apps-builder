"use client";

import { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
   ChevronLeft,
   ChevronRight,
   Plus,
   Calendar as CalendarIcon,
} from "lucide-react";
import { BlockComponentProps } from "./index";
import { CalendarProps } from "@/types/blueprint";

interface CalendarEvent {
   id: string;
   [key: string]: any;
}

type ViewType = "month" | "week" | "day" | "agenda";

export function CalendarBlock({
   block,
   data,
   loading,
   onAction,
}: BlockComponentProps) {
   const props = block.props as CalendarProps;
   const [currentDate, setCurrentDate] = useState(new Date());
   const [view, setView] = useState<ViewType>(
      (props.defaultView as ViewType) || "month"
   );

   const availableViews = props.views || ["month", "week", "day"];

   // Parse events from data
   const events = useMemo(() => {
      return (data || []).map((item) => ({
         ...item,
         start: new Date(item[props.startField]),
         end: new Date(item[props.endField]),
         title: item[props.titleField],
         color: props.colorField && props.colors
            ? props.colors[item[props.colorField]] || "#6366f1"
            : "#6366f1",
      }));
   }, [data, props]);

   // Calendar helpers
   const getDaysInMonth = (date: Date) => {
      const year = date.getFullYear();
      const month = date.getMonth();
      const firstDay = new Date(year, month, 1);
      const lastDay = new Date(year, month + 1, 0);
      const daysInMonth = lastDay.getDate();
      const startingDay = firstDay.getDay();

      const days: (Date | null)[] = [];

      // Add empty slots for days before the first of the month
      for (let i = 0; i < startingDay; i++) {
         days.push(null);
      }

      // Add days of the month
      for (let i = 1; i <= daysInMonth; i++) {
         days.push(new Date(year, month, i));
      }

      return days;
   };

   const getWeekDays = (date: Date) => {
      const start = new Date(date);
      start.setDate(date.getDate() - date.getDay());
      const days: Date[] = [];
      for (let i = 0; i < 7; i++) {
         const day = new Date(start);
         day.setDate(start.getDate() + i);
         days.push(day);
      }
      return days;
   };

   const getEventsForDate = (date: Date) => {
      return events.filter((event) => {
         const eventDate = event.start;
         return (
            eventDate.getFullYear() === date.getFullYear() &&
            eventDate.getMonth() === date.getMonth() &&
            eventDate.getDate() === date.getDate()
         );
      });
   };

   const navigateMonth = (direction: number) => {
      setCurrentDate((prev) => {
         const next = new Date(prev);
         next.setMonth(prev.getMonth() + direction);
         return next;
      });
   };

   const navigateWeek = (direction: number) => {
      setCurrentDate((prev) => {
         const next = new Date(prev);
         next.setDate(prev.getDate() + direction * 7);
         return next;
      });
   };

   const navigateDay = (direction: number) => {
      setCurrentDate((prev) => {
         const next = new Date(prev);
         next.setDate(prev.getDate() + direction);
         return next;
      });
   };

   const handleEventClick = (event: CalendarEvent) => {
      onAction?.("eventClick", { event }, { selectedRecord: event });
   };

   const handleSlotClick = (date: Date, hour?: number) => {
      const start = new Date(date);
      if (hour !== undefined) {
         start.setHours(hour, 0, 0, 0);
      }
      const end = new Date(start);
      end.setHours(start.getHours() + 1);

      onAction?.("slotClick", {
         start: start.toISOString(),
         end: end.toISOString(),
      });
   };

   const isToday = (date: Date) => {
      const today = new Date();
      return (
         date.getFullYear() === today.getFullYear() &&
         date.getMonth() === today.getMonth() &&
         date.getDate() === today.getDate()
      );
   };

   const formatMonthYear = (date: Date) => {
      return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
   };

   const weekDayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

   if (loading) {
      return (
         <Card className="p-6">
            <div className="animate-pulse">
               <div className="h-8 w-48 bg-white/10 rounded mb-6" />
               <div className="grid grid-cols-7 gap-2">
                  {Array(35)
                     .fill(0)
                     .map((_, i) => (
                        <div key={i} className="h-24 bg-white/5 rounded" />
                     ))}
               </div>
            </div>
         </Card>
      );
   }

   const renderMonthView = () => {
      const days = getDaysInMonth(currentDate);

      return (
         <div>
            {/* Week day headers */}
            <div className="grid grid-cols-7 gap-1 mb-2">
               {weekDayNames.map((day) => (
                  <div
                     key={day}
                     className="text-center text-sm font-medium text-white/60 py-2"
                  >
                     {day}
                  </div>
               ))}
            </div>

            {/* Calendar grid */}
            <div className="grid grid-cols-7 gap-1">
               {days.map((date, index) => {
                  if (!date) {
                     return <div key={`empty-${index}`} className="h-28" />;
                  }

                  const dayEvents = getEventsForDate(date);
                  const today = isToday(date);

                  return (
                     <div
                        key={date.toISOString()}
                        className={`h-28 p-1 rounded-lg border transition-colors cursor-pointer hover:bg-white/5 ${
                           today
                              ? "border-primary-500 bg-primary-500/10"
                              : "border-white/10"
                        }`}
                        onClick={() => props.allowCreate && handleSlotClick(date)}
                     >
                        <div
                           className={`text-sm mb-1 ${
                              today ? "text-primary-400 font-bold" : "text-white/60"
                           }`}
                        >
                           {date.getDate()}
                        </div>
                        <div className="space-y-0.5 overflow-hidden">
                           {dayEvents.slice(0, 3).map((event) => (
                              <div
                                 key={event.id}
                                 className="text-xs px-1 py-0.5 rounded truncate cursor-pointer hover:opacity-80"
                                 style={{ backgroundColor: event.color }}
                                 onClick={(e) => {
                                    e.stopPropagation();
                                    handleEventClick(event);
                                 }}
                              >
                                 {event.title}
                              </div>
                           ))}
                           {dayEvents.length > 3 && (
                              <div className="text-xs text-white/40 px-1">
                                 +{dayEvents.length - 3} more
                              </div>
                           )}
                        </div>
                     </div>
                  );
               })}
            </div>
         </div>
      );
   };

   const renderWeekView = () => {
      const days = getWeekDays(currentDate);
      const hours = Array.from({ length: 24 }, (_, i) => i);

      return (
         <div className="overflow-x-auto">
            <div className="min-w-[800px]">
               {/* Header */}
               <div className="grid grid-cols-8 gap-1 mb-2">
                  <div className="w-16" />
                  {days.map((date) => (
                     <div
                        key={date.toISOString()}
                        className={`text-center py-2 ${
                           isToday(date) ? "text-primary-400 font-bold" : "text-white/60"
                        }`}
                     >
                        <div className="text-sm">{weekDayNames[date.getDay()]}</div>
                        <div className="text-lg">{date.getDate()}</div>
                     </div>
                  ))}
               </div>

               {/* Time grid */}
               <div className="max-h-[600px] overflow-y-auto">
                  {hours.map((hour) => (
                     <div key={hour} className="grid grid-cols-8 gap-1">
                        <div className="w-16 text-xs text-white/40 text-right pr-2 py-2">
                           {hour.toString().padStart(2, "0")}:00
                        </div>
                        {days.map((date) => {
                           const dayEvents = getEventsForDate(date).filter(
                              (e) => e.start.getHours() === hour
                           );

                           return (
                              <div
                                 key={`${date.toISOString()}-${hour}`}
                                 className="h-12 border-t border-white/5 hover:bg-white/5 cursor-pointer relative"
                                 onClick={() =>
                                    props.allowCreate && handleSlotClick(date, hour)
                                 }
                              >
                                 {dayEvents.map((event) => (
                                    <div
                                       key={event.id}
                                       className="absolute inset-x-0 top-0 text-xs p-1 rounded truncate cursor-pointer hover:opacity-80 z-10"
                                       style={{
                                          backgroundColor: event.color,
                                          height: `${
                                             ((event.end.getHours() - event.start.getHours()) ||
                                                1) * 48
                                          }px`,
                                       }}
                                       onClick={(e) => {
                                          e.stopPropagation();
                                          handleEventClick(event);
                                       }}
                                    >
                                       {event.title}
                                    </div>
                                 ))}
                              </div>
                           );
                        })}
                     </div>
                  ))}
               </div>
            </div>
         </div>
      );
   };

   const renderDayView = () => {
      const hours = Array.from({ length: 24 }, (_, i) => i);
      const dayEvents = getEventsForDate(currentDate);

      return (
         <div>
            <div className="text-center mb-4">
               <div className="text-lg font-medium text-white">
                  {currentDate.toLocaleDateString("en-US", {
                     weekday: "long",
                     month: "long",
                     day: "numeric",
                  })}
               </div>
            </div>

            <div className="max-h-[600px] overflow-y-auto">
               {hours.map((hour) => {
                  const hourEvents = dayEvents.filter(
                     (e) => e.start.getHours() === hour
                  );

                  return (
                     <div key={hour} className="flex gap-4">
                        <div className="w-16 text-sm text-white/40 text-right py-3">
                           {hour.toString().padStart(2, "0")}:00
                        </div>
                        <div
                           className="flex-1 min-h-[48px] border-t border-white/5 hover:bg-white/5 cursor-pointer relative"
                           onClick={() =>
                              props.allowCreate && handleSlotClick(currentDate, hour)
                           }
                        >
                           {hourEvents.map((event) => (
                              <div
                                 key={event.id}
                                 className="absolute inset-x-0 top-0 p-2 rounded cursor-pointer hover:opacity-80"
                                 style={{
                                    backgroundColor: event.color,
                                    height: `${
                                       ((event.end.getHours() - event.start.getHours()) || 1) *
                                       48
                                    }px`,
                                 }}
                                 onClick={(e) => {
                                    e.stopPropagation();
                                    handleEventClick(event);
                                 }}
                              >
                                 <div className="font-medium">{event.title}</div>
                                 <div className="text-sm opacity-80">
                                    {event.start.toLocaleTimeString([], {
                                       hour: "2-digit",
                                       minute: "2-digit",
                                    })}{" "}
                                    -{" "}
                                    {event.end.toLocaleTimeString([], {
                                       hour: "2-digit",
                                       minute: "2-digit",
                                    })}
                                 </div>
                              </div>
                           ))}
                        </div>
                     </div>
                  );
               })}
            </div>
         </div>
      );
   };

   const renderAgendaView = () => {
      const upcomingEvents = events
         .filter((e) => e.start >= new Date())
         .sort((a, b) => a.start.getTime() - b.start.getTime())
         .slice(0, 20);

      return (
         <div className="space-y-2">
            {upcomingEvents.length === 0 ? (
               <div className="text-center py-12 text-white/40">
                  No upcoming events
               </div>
            ) : (
               upcomingEvents.map((event) => (
                  <div
                     key={event.id}
                     className="flex items-center gap-4 p-3 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-colors"
                     onClick={() => handleEventClick(event)}
                  >
                     <div
                        className="w-1 h-12 rounded-full"
                        style={{ backgroundColor: event.color }}
                     />
                     <div className="flex-1">
                        <div className="font-medium text-white">{event.title}</div>
                        <div className="text-sm text-white/60">
                           {event.start.toLocaleDateString()} at{" "}
                           {event.start.toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                           })}
                        </div>
                     </div>
                  </div>
               ))
            )}
         </div>
      );
   };

   return (
      <Card className="p-4">
         {/* Header */}
         <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
               <div className="flex items-center gap-1">
                  <Button
                     variant="ghost"
                     size="sm"
                     onClick={() =>
                        view === "month"
                           ? navigateMonth(-1)
                           : view === "week"
                           ? navigateWeek(-1)
                           : navigateDay(-1)
                     }
                  >
                     <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <Button
                     variant="ghost"
                     size="sm"
                     onClick={() =>
                        view === "month"
                           ? navigateMonth(1)
                           : view === "week"
                           ? navigateWeek(1)
                           : navigateDay(1)
                     }
                  >
                     <ChevronRight className="w-4 h-4" />
                  </Button>
               </div>
               <h2 className="text-lg font-semibold text-white">
                  {formatMonthYear(currentDate)}
               </h2>
               <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setCurrentDate(new Date())}
               >
                  Today
               </Button>
            </div>

            <div className="flex items-center gap-2">
               {/* View switcher */}
               <div className="flex rounded-lg bg-white/5 p-1">
                  {availableViews.map((v) => (
                     <button
                        key={v}
                        onClick={() => setView(v as ViewType)}
                        className={`px-3 py-1 text-sm rounded-md transition-colors ${
                           view === v
                              ? "bg-primary-500 text-white"
                              : "text-white/60 hover:text-white"
                        }`}
                     >
                        {v.charAt(0).toUpperCase() + v.slice(1)}
                     </button>
                  ))}
               </div>

               {props.allowCreate && (
                  <Button
                     size="sm"
                     onClick={() => handleSlotClick(new Date())}
                  >
                     <Plus className="w-4 h-4 mr-2" />
                     Add Event
                  </Button>
               )}
            </div>
         </div>

         {/* Calendar content */}
         {view === "month" && renderMonthView()}
         {view === "week" && renderWeekView()}
         {view === "day" && renderDayView()}
         {view === "agenda" && renderAgendaView()}
      </Card>
   );
}

