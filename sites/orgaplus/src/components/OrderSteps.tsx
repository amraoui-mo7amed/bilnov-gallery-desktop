import React from "react"
import { motion } from "framer-motion"
import { useLanguage } from "@/context/LanguageContext"
import { Button } from "@/components/ui/Button"
import { Badge } from "@/components/ui/Badge"
import { MessageCircle, BadgeCheck, KeyRound } from "lucide-react"

export const OrderSteps: React.FC<{ onOpenOrderModal: () => void }> = ({ onOpenOrderModal }) => {
  const { t } = useLanguage()
  const steps = [
    { icon: MessageCircle, title: t("step1Title"), desc: t("step1Desc"), color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
    { icon: BadgeCheck, title: t("step2Title"), desc: t("step2Desc"), color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20" },
    { icon: KeyRound, title: t("step3Title"), desc: t("step3Desc"), color: "text-purple-400 bg-purple-500/10 border-purple-500/20" },
  ]

  return (
    <section id="order" className="py-16 sm:py-24">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-10 sm:mb-14 space-y-4">
          <Badge variant="purple" className="px-3.5 py-1 text-xs">{t("orderBadge")}</Badge>
          <h2 className="text-2xl sm:text-4xl lg:text-5xl font-extrabold text-foreground tracking-tight">{t("orderTitle")}</h2>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">{t("orderSubtitle")}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
          {steps.map((s, i) => {
            const Icon = s.icon
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.12 }}
                className="relative rounded-3xl border border-border bg-card p-6 sm:p-8 space-y-4"
              >
                <span className="absolute top-4 end-5 text-5xl font-black text-muted-foreground/15">{i + 1}</span>
                <div className={`inline-flex p-3.5 rounded-2xl border ${s.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-foreground">{s.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{s.desc}</p>
              </motion.div>
            )
          })}
        </div>

        <div className="mt-10 flex justify-center">
          <Button variant="whatsapp" size="lg" onClick={onOpenOrderModal} className="gap-3 font-bold w-full sm:w-auto shadow-xl shadow-emerald-600/30">
            <MessageCircle className="w-5 h-5" />
            <span>{t("navOrderNow")}</span>
          </Button>
        </div>
      </div>
    </section>
  )
}
