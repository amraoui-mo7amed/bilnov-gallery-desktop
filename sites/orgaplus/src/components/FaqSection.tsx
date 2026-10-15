import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useLanguage } from "@/context/LanguageContext"
import { Badge } from "@/components/ui/Badge"
import { ChevronDown } from "lucide-react"

export const FaqSection: React.FC = () => {
  const { t } = useLanguage()
  const [openIndex, setOpenIndex] = useState<number | null>(0)

  const faqs = [
    { q: t("faq1Q"), a: t("faq1A") },
    { q: t("faq2Q"), a: t("faq2A") },
    { q: t("faq3Q"), a: t("faq3A") },
    { q: t("faq4Q"), a: t("faq4A") },
    { q: t("faq5Q"), a: t("faq5A") },
  ]

  return (
    <section id="faq" className="py-16 sm:py-24 bg-muted/20">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10 sm:mb-14 space-y-4">
          <Badge variant="purple" className="px-3.5 py-1 text-xs">{t("faqBadge")}</Badge>
          <h2 className="text-2xl sm:text-4xl lg:text-5xl font-extrabold text-foreground tracking-tight">{t("faqTitle")}</h2>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">{t("faqSubtitle")}</p>
        </div>

        <div className="space-y-3 sm:space-y-4">
          {faqs.map((faq, idx) => {
            const isOpen = openIndex === idx
            return (
              <div key={idx} className="rounded-2xl border border-border bg-card overflow-hidden">
                <button
                  onClick={() => setOpenIndex(isOpen ? null : idx)}
                  className="w-full p-4 sm:p-6 text-start flex items-center justify-between gap-4"
                >
                  <span className="text-sm sm:text-base font-bold text-foreground">{faq.q}</span>
                  <div className={`w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0 transition-transform ${isOpen ? "rotate-180 text-indigo-400" : "text-muted-foreground"}`}>
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </button>
                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }} className="overflow-hidden">
                      <div className="px-4 sm:px-6 pb-5 sm:pb-6 pt-3 text-sm text-muted-foreground leading-relaxed border-t border-border/40">{faq.a}</div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
