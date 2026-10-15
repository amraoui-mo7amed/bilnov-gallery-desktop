import React from "react"
import { MessageCircle } from "lucide-react"

export const FloatingWhatsApp: React.FC<{ onOpenOrderModal: () => void }> = ({ onOpenOrderModal }) => (
  <button
    onClick={onOpenOrderModal}
    className="fixed bottom-20 sm:bottom-6 end-4 sm:end-6 z-40 p-3.5 sm:p-4 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white shadow-2xl shadow-emerald-600/50 hover:scale-105 active:scale-95 transition-all"
    aria-label="Order orga+ on WhatsApp"
  >
    <span className="absolute -inset-1 rounded-2xl bg-emerald-500 opacity-30 animate-ping -z-10" />
    <MessageCircle className="w-6 h-6 sm:w-7 sm:h-7" />
  </button>
)
