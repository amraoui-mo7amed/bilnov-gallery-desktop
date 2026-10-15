import React from "react"
import { useLanguage } from "@/context/LanguageContext"
import { Button } from "@/components/ui/Button"
import { MessageCircle } from "lucide-react"

export const BottomCta: React.FC<{ onOpenOrderModal: () => void }> = ({ onOpenOrderModal }) => {
  const { t } = useLanguage()

  return (
    <section className="pt-12 sm:pt-20 pb-24 sm:pb-28">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative rounded-3xl p-6 sm:p-14 lg:p-20 overflow-hidden bg-gradient-to-br from-indigo-900/70 via-[#111827] to-purple-950/70 border border-indigo-500/30 shadow-2xl text-center">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(600px,100%)] h-[300px] bg-indigo-500/20 blur-[120px] pointer-events-none rounded-full" />
          <div className="relative max-w-3xl mx-auto space-y-5 sm:space-y-6">
            <h2 className="text-2xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight leading-tight">{t("ctaTitle")}</h2>
            <p className="text-sm sm:text-lg text-slate-300 leading-relaxed max-w-2xl mx-auto">{t("ctaSubtitle")}</p>
            <div className="flex justify-center pt-2 max-w-md mx-auto">
              <Button variant="whatsapp" size="lg" onClick={onOpenOrderModal} className="w-full sm:w-auto gap-3 font-bold shadow-xl shadow-emerald-600/40">
                <MessageCircle className="w-5 h-5" />
                <span>{t("ctaButton")}</span>
              </Button>
            </div>
            <p className="text-xs text-slate-400">{t("ctaNote")}</p>
          </div>
        </div>
      </div>
    </section>
  )
}
