import React from "react"
import { motion } from "framer-motion"
import { useLanguage } from "@/context/LanguageContext"
import { Badge } from "@/components/ui/Badge"
import { FolderTree, Box, Fingerprint, ExternalLink, ShieldCheck, Monitor } from "lucide-react"

export const FeaturesSection: React.FC = () => {
  const { t } = useLanguage()

  const features = [
    { icon: FolderTree, title: t("feature1Title"), desc: t("feature1Desc"), color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20" },
    { icon: Box, title: t("feature2Title"), desc: t("feature2Desc"), color: "text-purple-400 bg-purple-500/10 border-purple-500/20" },
    { icon: Fingerprint, title: t("feature3Title"), desc: t("feature3Desc"), color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
    { icon: ExternalLink, title: t("feature4Title"), desc: t("feature4Desc"), color: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20" },
    { icon: ShieldCheck, title: t("feature5Title"), desc: t("feature5Desc"), color: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
    { icon: Monitor, title: t("feature6Title"), desc: t("feature6Desc"), color: "text-sky-400 bg-sky-500/10 border-sky-500/20" },
  ]

  return (
    <section id="features" className="py-16 sm:py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-10 sm:mb-14 space-y-4">
          <Badge className="px-3.5 py-1 text-xs">{t("featuresBadge")}</Badge>
          <h2 className="text-2xl sm:text-4xl lg:text-5xl font-extrabold text-foreground tracking-tight">{t("featuresTitle")}</h2>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">{t("featuresSubtitle")}</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
          {features.map((f, i) => {
            const Icon = f.icon
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: (i % 3) * 0.1 }}
                className="group rounded-3xl border border-border bg-card p-6 sm:p-8 hover:border-indigo-500/40 hover:shadow-xl hover:shadow-indigo-500/5 transition-all space-y-4"
              >
                <div className={`inline-flex p-3.5 rounded-2xl border ${f.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg sm:text-xl font-bold text-foreground group-hover:text-indigo-400 transition-colors">{f.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
