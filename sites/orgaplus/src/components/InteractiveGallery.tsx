import React, { useState, useMemo } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useLanguage } from "@/context/LanguageContext"
import { mockAssets, type Asset } from "@/data/mockAssets"
import { AssetVisual } from "@/components/AssetVisual"
import { Badge } from "@/components/ui/Badge"
import { Search, FolderOpen, CheckCircle2, Maximize2, X, Images } from "lucide-react"

export const InteractiveGallery: React.FC = () => {
  const { t } = useLanguage()
  const [query, setQuery] = useState("")
  const [job, setJob] = useState("all")
  const [open, setOpen] = useState<Asset | null>(null)
  const [activeImage, setActiveImage] = useState<string | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  const handleOpen = (asset: Asset) => {
    setOpen(asset)
    setActiveImage(asset.imageUrl)
  }

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim()
    return mockAssets.filter(
      (a) =>
        (job === "all" || a.job === job) &&
        (!q ||
          [a.title, a.category, a.subcategory, a.format].some((s) => s.toLowerCase().includes(q)))
    )
  }, [query, job])

  const showToast = (path: string) => {
    setToast(`${t("galleryToast")} ${path}`)
    setTimeout(() => setToast(null), 3000)
  }

  const tabs = [
    { id: "all", label: t("galleryAll") },
    { id: "architect", label: t("jobArchitect") },
    { id: "graphiste", label: t("jobGraphiste") },
    { id: "video_maker", label: t("jobVideoMaker") },
  ]

  return (
    <section id="gallery" className="py-16 sm:py-24 bg-muted/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-10 sm:mb-12 space-y-4">
          <Badge variant="purple" className="px-3.5 py-1 text-xs">{t("galleryBadge")}</Badge>
          <h2 className="text-2xl sm:text-4xl lg:text-5xl font-extrabold text-foreground tracking-tight">{t("galleryTitle")}</h2>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">{t("gallerySubtitle")}</p>
        </div>

        <div className="rounded-2xl border border-border bg-card p-3 sm:p-5 shadow-lg mb-8 flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          <div className="relative w-full lg:w-96">
            <Search className="w-4 h-4 text-muted-foreground absolute top-1/2 -translate-y-1/2 start-3.5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("gallerySearchPlaceholder")}
              className="w-full h-11 ps-10 pe-9 rounded-xl border border-border bg-background text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {query && (
              <button onClick={() => setQuery("")} className="absolute top-1/2 -translate-y-1/2 end-3 text-muted-foreground hover:text-foreground">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0">
            {tabs.map((b) => (
              <button
                key={b.id}
                onClick={() => setJob(b.id)}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  job === b.id ? "bg-primary text-primary-foreground shadow-md shadow-indigo-500/20" : "bg-muted text-muted-foreground hover:bg-accent hover:text-foreground"
                }`}
              >
                {b.label}
              </button>
            ))}
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="text-center py-16 rounded-3xl border border-dashed border-border bg-card/50">
            <Search className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
            <h3 className="text-base sm:text-lg font-bold text-foreground">{t("galleryEmpty")}</h3>
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
            {filtered.map((a) => (
              <motion.div
                key={a.id}
                layout
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="group rounded-2xl border border-border bg-card overflow-hidden hover:border-indigo-500/50 hover:shadow-2xl hover:shadow-indigo-500/10 transition-all flex flex-col"
              >
                <button onClick={() => handleOpen(a)} className="aspect-[4/3] relative overflow-hidden block w-full text-start">
                  <AssetVisual kind={a.kind} imageUrl={a.imageUrl} alt={a.title} className="group-hover:scale-105 transition-transform duration-500" />
                  <div className="absolute top-2 start-2 max-w-[85%] truncate px-2 py-0.5 rounded-full bg-[#0A0E1A]/85 border border-white/10 text-[10px] sm:text-[11px] font-bold text-indigo-300">
                    {a.category} · {a.subcategory}
                  </div>
                  {a.imageUrls && a.imageUrls.length > 1 && (
                    <div className="absolute bottom-2 start-2 px-1.5 py-0.5 rounded-md bg-black/80 backdrop-blur-sm border border-white/10 text-white/90 text-[10px] font-medium flex items-center gap-1 shadow-sm">
                      <Images className="w-3 h-3 text-indigo-400" />
                      <span>{a.imageUrls.length}</span>
                    </div>
                  )}
                  <div className="absolute bottom-2 end-2 px-1.5 py-0.5 rounded-md bg-indigo-600 text-white text-[10px] font-mono font-bold uppercase">{a.format}</div>
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="p-2.5 rounded-full bg-white/20 text-white"><Maximize2 className="w-4 h-4" /></span>
                  </div>
                </button>
                <div className="p-3 sm:p-4 space-y-2 flex-1 flex flex-col justify-between">
                  <div>
                    <h3 className="text-xs sm:text-sm font-bold text-foreground line-clamp-1">{a.title}</h3>
                    <div className="text-[11px] font-mono text-muted-foreground">{a.size}</div>
                  </div>
                  <div className="pt-2 border-t border-border/60 flex items-center justify-between gap-2">
                    <span className="hidden sm:flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5" /> {t("galleryHasModel")}
                    </span>
                    <button
                      onClick={() => showToast(a.depthPath)}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] sm:text-xs font-semibold text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                    >
                      <FolderOpen className="w-3.5 h-3.5" />
                      <span>{t("galleryOpenFolder")}</span>
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-[60] bg-black/90 backdrop-blur-md flex items-center justify-center p-3 sm:p-8"
              onClick={() => setOpen(null)}
            >
              <div
                className="relative max-w-3xl w-full max-h-[92vh] overflow-y-auto bg-[#0A0E1A] border border-white/10 rounded-3xl shadow-2xl p-4 sm:p-6 space-y-4"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="text-base sm:text-lg font-bold text-white truncate">{open.title}</h3>
                    <span dir="ltr" className="text-[11px] sm:text-xs font-mono text-indigo-400 break-all block">{open.depthPath}</span>
                  </div>
                  <button onClick={() => setOpen(null)} className="p-2 rounded-xl bg-white/10 text-white hover:bg-white/20 shrink-0">
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="aspect-[16/10] rounded-2xl overflow-hidden border border-white/10">
                  <AssetVisual kind={open.kind} imageUrl={activeImage || open.imageUrl} alt={open.title} />
                </div>

                {open.imageUrls && open.imageUrls.length > 1 && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-muted-foreground px-0.5">
                      <span className="font-semibold text-white/80">{open.imageUrls.length} {t("galleryAngles")}</span>
                      <span className="font-mono text-[11px] text-indigo-400">
                        {((open.imageUrls.indexOf(activeImage || open.imageUrl)) + 1)} / {open.imageUrls.length}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
                      {open.imageUrls.map((img, idx) => {
                        const isCurrent = (activeImage || open.imageUrl) === img
                        return (
                          <button
                            key={idx}
                            onClick={() => setActiveImage(img)}
                            className={`relative w-16 sm:w-20 aspect-[4/3] rounded-xl overflow-hidden border-2 transition-all shrink-0 ${
                              isCurrent
                                ? "border-indigo-500 ring-2 ring-indigo-500/40 scale-105"
                                : "border-white/10 opacity-60 hover:opacity-100 hover:border-white/30"
                            }`}
                          >
                            <img src={img} alt="" className="w-full h-full object-cover" />
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                  <span className="text-xs font-mono text-emerald-400 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                    {open.format} · {open.size}
                  </span>
                  <button
                    onClick={() => {
                      showToast(open.depthPath)
                      setOpen(null)
                    }}
                    className="px-4 py-2.5 rounded-xl bg-primary text-white text-xs font-bold hover:bg-primary-hover flex items-center gap-2"
                  >
                    <FolderOpen className="w-4 h-4" />
                    <span>{t("galleryOpenFolder")}</span>
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {toast && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 30 }}
              className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[70] w-[92vw] max-w-lg px-4 py-3 rounded-2xl bg-[#0A0E1A] text-white border border-indigo-500/40 shadow-2xl flex items-center gap-3 text-xs"
            >
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
              <span dir="ltr" className="font-mono break-all">{toast}</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  )
}
