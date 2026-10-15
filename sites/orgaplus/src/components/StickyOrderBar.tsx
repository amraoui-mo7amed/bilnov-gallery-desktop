import React, { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useLanguage } from "@/context/LanguageContext"
import { Button } from "@/components/ui/Button"
import { MessageCircle, X } from "lucide-react"

export const StickyOrderBar: React.FC<{ onOpenOrderModal: () => void }> = ({ onOpenOrderModal }) => {
  const { t } = useLanguage()
  const [scrolled, setScrolled] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 600)
    window.addEventListener("scroll", onScroll)
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  return (
    <AnimatePresence>
      {scrolled && !dismissed && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          className="fixed bottom-0 inset-x-0 z-30 bg-card/95 border-t border-border shadow-2xl backdrop-blur-lg px-3 sm:px-4 py-2.5"
        >
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <img src="/icon.png" alt="orga+" className="w-9 h-9 rounded-xl shrink-0" />
              <div className="min-w-0">
                <div className="text-sm font-bold text-foreground truncate">{t("stickyText")}</div>
                <div className="text-xs text-muted-foreground truncate">{t("stickySub")}</div>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Button variant="whatsapp" size="sm" onClick={onOpenOrderModal} className="gap-2 font-bold h-10 px-4">
                <MessageCircle className="w-4 h-4" />
                <span>{t("stickyButton")}</span>
              </Button>
              <button onClick={() => setDismissed(true)} className="p-2 rounded-lg text-muted-foreground hover:text-foreground" aria-label="Dismiss">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
