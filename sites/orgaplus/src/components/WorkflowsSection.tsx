import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useLanguage } from "@/context/LanguageContext"
import { mockAssets } from "@/data/mockAssets"
import { AssetVisual } from "@/components/AssetVisual"
import { Button } from "@/components/ui/Button"
import { Badge } from "@/components/ui/Badge"
import { Compass, Palette, Film, CheckCircle2, MessageCircle } from "lucide-react"

interface Props {
  onOpenOrderModal: () => void
}

type Job = "architect" | "graphiste" | "video_maker"

export const WorkflowsSection: React.FC<Props> = ({ onOpenOrderModal }) => {
  const { t } = useLanguage()
  const [active, setActive] = useState<Job>("architect")

  const jobs = {
    architect: {
      label: t("jobArchitect"),
      title: t("jobArchitectTitle"),
      desc: t("jobArchitectDesc"),
      icon: Compass,
      accent: "text-indigo-400",
      bg: "bg-indigo-500/10 border-indigo-500/30",
      formats: [".skp", ".max", ".obj", ".fbx", ".zip"],
    },
    graphiste: {
      label: t("jobGraphiste"),
      title: t("jobGraphisteTitle"),
      desc: t("jobGraphisteDesc"),
      icon: Palette,
      accent: "text-purple-400",
      bg: "bg-purple-500/10 border-purple-500/30",
      formats: [".blend", ".obj", ".png", ".webp", ".rar"],
    },
    video_maker: {
      label: t("jobVideoMaker"),
      title: t("jobVideoMakerTitle"),
      desc: t("jobVideoMakerDesc"),
      icon: Film,
      accent: "text-cyan-400",
      bg: "bg-cyan-500/10 border-cyan-500/30",
      formats: [".c4d", ".glb", ".gltf", ".fbx", ".7z"],
    },
  }

  const cur = jobs[active]
  const Icon = cur.icon
  const previews = mockAssets.filter((a) => a.job === active).slice(0, 2)
  const points = [t("workflowPoint1"), t("workflowPoint2"), t("workflowPoint3"), t("workflowPoint4")]

  return (
    <section id="workflows" className="py-16 sm:py-24 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-10 sm:mb-14 space-y-4">
          <Badge variant="purple" className="px-3.5 py-1 text-xs">{t("workflowsBadge")}</Badge>
          <h2 className="text-2xl sm:text-4xl lg:text-5xl font-extrabold text-foreground tracking-tight">{t("workflowsTitle")}</h2>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">{t("workflowsSubtitle")}</p>
        </div>

        <div className="grid grid-cols-3 sm:flex sm:justify-center gap-2 sm:gap-4 mb-8 sm:mb-12">
          {(Object.keys(jobs) as Job[]).map((id) => {
            const j = jobs[id]
            const TabIcon = j.icon
            const on = active === id
            return (
              <button
                key={id}
                onClick={() => setActive(id)}
                className={`flex flex-col sm:flex-row items-center justify-center gap-1.5 sm:gap-2.5 px-2 sm:px-6 py-3 sm:py-3.5 rounded-2xl text-xs sm:text-sm font-bold transition-all border ${
                  on
                    ? "bg-card text-foreground border-indigo-500 shadow-xl shadow-indigo-500/15"
                    : "bg-card/40 text-muted-foreground border-border hover:bg-card/80"
                }`}
              >
                <TabIcon className={`w-4 h-4 ${on ? "text-indigo-400" : ""}`} />
                <span className="text-center leading-tight">{j.label}</span>
              </button>
            )
          })}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="rounded-3xl border border-border bg-card p-5 sm:p-8 lg:p-10 shadow-2xl"
          >
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
              <div className="lg:col-span-7 space-y-5">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-2xl border ${cur.bg} shrink-0`}>
                    <Icon className={`w-6 h-6 sm:w-7 sm:h-7 ${cur.accent}`} />
                  </div>
                  <h3 className="text-xl sm:text-3xl font-extrabold text-foreground leading-tight">{cur.title}</h3>
                </div>
                <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">{cur.desc}</p>

                <div className="space-y-2">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">{t("supportedFormats")}</span>
                  <div className="flex flex-wrap gap-2">
                    {cur.formats.map((f) => (
                      <span key={f} className="px-3 py-1 rounded-lg text-xs font-mono font-bold bg-muted border border-border text-foreground">{f}</span>
                    ))}
                  </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-3 pt-1">
                  {points.map((p) => (
                    <div key={p} className="flex items-start gap-2.5">
                      <CheckCircle2 className="w-4 h-4 mt-0.5 text-emerald-400 shrink-0" />
                      <span className="text-sm text-foreground/90 font-medium">{p}</span>
                    </div>
                  ))}
                </div>

                <div className="pt-2">
                  <Button variant="whatsapp" onClick={onOpenOrderModal} className="gap-2 font-bold w-full sm:w-auto">
                    <MessageCircle className="w-4 h-4" />
                    <span>{t("workflowOrderCta")}</span>
                  </Button>
                </div>
              </div>

              <div className="lg:col-span-5 grid grid-cols-2 gap-3 sm:gap-4">
                {previews.map((a) => (
                  <div key={a.id} className="rounded-2xl overflow-hidden border border-border shadow-lg">
                    <div className="aspect-[3/4]">
                      <AssetVisual kind={a.kind} imageUrl={a.imageUrl} alt={a.title} />
                    </div>
                    <div className="p-2.5 bg-background/60">
                      <div className="text-xs font-bold text-foreground truncate">{a.title}</div>
                      <div className="text-[10px] font-mono text-muted-foreground">{a.format}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  )
}
