import React from "react"
import { motion } from "framer-motion"
import { useLanguage } from "@/context/LanguageContext"
import { mockAssets } from "@/data/mockAssets"
import { AssetVisual } from "@/components/AssetVisual"
import { Button } from "@/components/ui/Button"
import {
  MessageCircle,
  ShieldCheck,
  CheckCircle2,
  FolderOpen,
  HardDrive,
  Minus,
  Square,
  X,
} from "lucide-react"

interface HeroProps {
  onOpenOrderModal: () => void
}

export const Hero: React.FC<HeroProps> = ({ onOpenOrderModal }) => {
  const { t, isRTL } = useLanguage()
  const cards = [mockAssets[0], mockAssets[1], mockAssets[2]]

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

        {/* Windows app mockup */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="relative mt-12 sm:mt-16 max-w-5xl mx-auto"
        >
          <div className="absolute -inset-1 rounded-[2rem] bg-gradient-to-r from-indigo-500/30 via-purple-500/20 to-cyan-500/30 blur-2xl opacity-70" />

          <div className="relative rounded-2xl border border-border/80 bg-card/95 backdrop-blur-xl shadow-2xl overflow-hidden">
            {/* Windows title bar */}
            <div dir="ltr" className="h-10 sm:h-11 bg-muted/60 dark:bg-[#111827] border-b border-border/80 flex items-center justify-between">
              <div className="flex items-center gap-2 px-3 sm:px-4 min-w-0">
                <img src="/icon.png" alt="" className="w-4 h-4 rounded-sm" />
                <span className="text-[11px] sm:text-xs font-medium text-muted-foreground truncate">orga+</span>
              </div>
              <div className="flex h-full shrink-0">
                <span className="w-10 sm:w-12 flex items-center justify-center text-muted-foreground"><Minus className="w-3.5 h-3.5" /></span>
                <span className="w-10 sm:w-12 flex items-center justify-center text-muted-foreground"><Square className="w-3 h-3" /></span>
                <span className="w-10 sm:w-12 flex items-center justify-center text-muted-foreground hover:bg-red-500 hover:text-white transition-colors"><X className="w-4 h-4" /></span>
              </div>
            </div>

            {/* Toolbar */}
            <div className="px-3 sm:px-5 py-3 border-b border-border/60 bg-muted/20 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-600 text-white">{t("galleryAll")}</span>
                <span className="px-2.5 py-1 rounded-lg text-xs font-medium text-muted-foreground bg-muted/60">{t("jobArchitect")}</span>
                <span className="px-2.5 py-1 rounded-lg text-xs font-medium text-muted-foreground bg-muted/60 hidden min-[420px]:inline-block">{t("jobGraphiste")}</span>
                <span className="px-2.5 py-1 rounded-lg text-xs font-medium text-muted-foreground bg-muted/60 hidden sm:inline-block">{t("jobVideoMaker")}</span>
              </div>
              <div dir="ltr" className="hidden sm:flex items-center gap-2 text-xs font-mono text-muted-foreground">
                <HardDrive className="w-3.5 h-3.5 text-indigo-400" />
                <span>C:\Library</span>
              </div>
            </div>

            {/* Cards */}
            <div className="p-3 sm:p-6 grid grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-6 bg-background/50 dark:bg-[#0A0E1A]/60">
              {cards.map((a, i) => (
                <div
                  key={a.id}
                  className={`group rounded-xl border border-border bg-card overflow-hidden hover:border-indigo-500/50 transition-colors ${
                    i === 2 ? "hidden lg:block" : ""
                  }`}
                >
                  <div className="aspect-[4/3] relative">
                    <AssetVisual kind={a.kind} imageUrl={a.imageUrl} alt={a.title} />
                    <div className="absolute top-2 left-2 max-w-[85%] truncate px-2 py-0.5 rounded-full bg-[#0A0E1A]/85 border border-white/10 text-[10px] sm:text-[11px] font-bold text-indigo-300">
                      {a.category} · {a.subcategory}
                    </div>
                    <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded-md bg-indigo-600 text-white text-[10px] font-mono font-bold uppercase">
                      {a.format}
                    </div>
                  </div>
                  <div className="p-2.5 sm:p-3.5 space-y-2">
                    <h4 className="text-xs sm:text-sm font-bold text-foreground truncate">{a.title}</h4>
                    <div className="flex items-center justify-between pt-1.5 border-t border-border/50">
                      <span className="text-emerald-400 font-semibold flex items-center gap-1 text-[10px] sm:text-[11px]">
                        <CheckCircle2 className="w-3 h-3" /> {t("galleryHasModel")}
                      </span>
                      <span className="text-[10px] sm:text-[11px] font-semibold text-indigo-400 flex items-center gap-1">
                        <FolderOpen className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div
            className={`hidden md:flex items-center gap-3 absolute -bottom-5 ${
              isRTL ? "-left-3" : "-right-3"
            } p-3 rounded-2xl border border-emerald-500/30 bg-[#0A0E1A]/95 text-white shadow-2xl backdrop-blur-xl animate-float`}
          >
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div className="text-xs font-bold text-emerald-300">{t("feature3Title")}</div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
