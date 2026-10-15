import React from "react"
import { motion } from "framer-motion"
import { useLanguage } from "@/context/LanguageContext"
import { Button } from "@/components/ui/Button"
import { MessageCircle, CheckCircle2 } from "lucide-react"

interface HeroProps {
  onOpenOrderModal: () => void
}

export const Hero: React.FC<HeroProps> = ({ onOpenOrderModal }) => {
  const { t } = useLanguage()

  return (
    <section className="relative pt-28 pb-16 sm:pt-36 sm:pb-24 overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[min(700px,100vw)] h-[400px] bg-indigo-600/15 dark:bg-indigo-600/20 blur-[120px] -z-10 rounded-full pointer-events-none" />
      <div className="absolute top-1/2 right-0 w-[300px] h-[300px] bg-cyan-500/10 dark:bg-cyan-500/15 blur-[100px] -z-10 rounded-full pointer-events-none" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:32px_32px] -z-20" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-4xl mx-auto space-y-5 sm:space-y-6">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-3xl min-[400px]:text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-foreground leading-[1.15]"
          >
            {t("heroTitlePrefix")}{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400">
              {t("heroTitleHighlight")}
            </span>{" "}
            {t("heroTitleSuffix")}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-base sm:text-lg lg:text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed"
          >
            {t("heroSubtitle")}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-3 sm:gap-4 pt-2 max-w-md sm:max-w-none mx-auto"
          >
            <Button variant="whatsapp" size="lg" onClick={onOpenOrderModal} className="gap-3 text-base shadow-xl shadow-emerald-600/30 font-bold px-8">
              <MessageCircle className="w-5 h-5" />
              <span>{t("heroCtaOrder")}</span>
            </Button>
          </motion.div>

          <p className="text-xs text-muted-foreground flex items-center justify-center gap-2 px-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>{t("heroTrustText")}</span>
          </p>
        </div>
      </div>
    </section>
  )
}
