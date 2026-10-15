import React, { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import confetti from "canvas-confetti"
import { useLanguage } from "@/context/LanguageContext"
import { Button } from "@/components/ui/Button"
import { X, MessageCircle, ShieldCheck, User, FileText } from "lucide-react"

interface OrderModalProps {
  isOpen: boolean
  onClose: () => void
}

export const OrderModal: React.FC<OrderModalProps> = ({ isOpen, onClose }) => {
  const { t, getWhatsAppUrl } = useLanguage()
  const [name, setName] = useState("")
  const [notes, setNotes] = useState("")

  useEffect(() => {
    if (!isOpen) return
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose()
    document.body.style.overflow = "hidden"
    window.addEventListener("keydown", onKey)
    return () => {
      document.body.style.overflow = ""
      window.removeEventListener("keydown", onKey)
    }
  }, [isOpen, onClose])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    try {
      confetti({ particleCount: 80, spread: 60, origin: { y: 0.6 } })
    } catch {
      /* ignore */
    }
    window.open(
      getWhatsAppUrl({ name: name.trim() || undefined, notes: notes.trim() || undefined }),
      "_blank"
    )
    onClose()
  }

  const field =
    "w-full px-3.5 rounded-xl border border-white/10 bg-white/5 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[80] flex items-end sm:items-center justify-center p-0 sm:p-6">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/80 backdrop-blur-md" onClick={onClose} />
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 40 }}
            transition={{ duration: 0.25 }}
            className="relative w-full max-w-lg max-h-[95vh] overflow-y-auto rounded-t-3xl sm:rounded-3xl border border-indigo-500/30 bg-[#0A0E1A] p-5 sm:p-8 shadow-2xl"
          >
            <button onClick={onClose} className="absolute top-4 end-4 p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white" aria-label="Close">
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3.5 mb-4 pe-10">
              <img src="/icon.png" alt="orga+" className="w-12 h-12 rounded-2xl shadow-lg shadow-indigo-500/30" />
              <div>
                <h3 className="text-lg sm:text-xl font-black text-white">{t("modalTitle")}</h3>
                <p className="text-xs text-slate-400">{t("modalSubtitle")}</p>
              </div>
            </div>

            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5"><User className="w-3.5 h-3.5 text-indigo-400" />{t("modalNameLabel")}</label>
                <input required value={name} onChange={(e) => setName(e.target.value)} placeholder={t("modalNamePlaceholder")} className={`${field} h-11`} />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5"><FileText className="w-3.5 h-3.5 text-emerald-400" />{t("modalNotesLabel")}</label>
                <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder={t("modalNotesPlaceholder")} className={`${field} p-3 resize-none`} />
              </div>
              <Button type="submit" variant="whatsapp" size="lg" className="w-full gap-2.5 font-bold shadow-xl shadow-emerald-600/30">
                <MessageCircle className="w-5 h-5" />
                <span>{t("modalSubmitBtn")}</span>
              </Button>
            </form>

            <div className="mt-5 pt-4 border-t border-white/10 flex items-center justify-center text-[11px] text-slate-400">
              <span className="flex items-center gap-1.5 text-emerald-400"><ShieldCheck className="w-4 h-4 shrink-0" />{t("modalGuarantee")}</span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
