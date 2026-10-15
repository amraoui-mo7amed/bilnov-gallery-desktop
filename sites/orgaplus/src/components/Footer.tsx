import React from "react"
import { useLanguage, WHATSAPP_DISPLAY, WHATSAPP_RAW_NUMBER } from "@/context/LanguageContext"
import { MessageCircle, Monitor } from "lucide-react"

const SOCIALS = [
  {
    name: "Facebook",
    href: "https://www.facebook.com/orgaplusdz",
    path: "M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.413c0-3.026 1.792-4.697 4.533-4.697 1.312 0 2.686.236 2.686.236v2.971H15.83c-1.491 0-1.956.931-1.956 1.886v2.264h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z",
  },
  {
    name: "Instagram",
    href: "https://www.instagram.com/orgaplus.dz/",
    path: "M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z",
  },
]

export const Footer: React.FC = () => {
  const { t } = useLanguage()
  const links = [
    ["#features", t("navFeatures")],
    ["#workflows", t("navWorkflows")],
    ["#order", t("navHowToOrder")],
    ["#faq", t("navFaq")],
  ]

  return (
    <footer className="border-t border-border bg-card/60 dark:bg-[#070B14] pt-12 sm:pt-16 pb-24 sm:pb-12 text-foreground">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 sm:gap-10 pb-10 border-b border-border">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <img src="/icon.png" alt="orga+ logo" className="w-10 h-10 rounded-2xl" />
              <span className="text-2xl font-black tracking-tight">orga<span className="text-indigo-500">+</span></span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">{t("footerDesc")}</p>
            <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
              <Monitor className="w-4 h-4 text-indigo-400" />
              <span>{t("footerWindows")}</span>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider">{t("footerQuickLinks")}</h4>
            <ul className="grid grid-cols-2 sm:grid-cols-1 gap-2 text-sm text-muted-foreground">
              {links.map(([href, label]) => (
                <li key={href}><a href={href} className="hover:text-indigo-400 transition-colors">{label}</a></li>
              ))}
            </ul>
          </div>

          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider">{t("footerContact")}</h4>
            <div className="space-y-3 text-sm">
              <a href={`https://wa.me/${WHATSAPP_RAW_NUMBER}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-600/15 border border-emerald-500/30 text-emerald-400 font-bold hover:bg-emerald-600/25 transition-colors">
                <MessageCircle className="w-4 h-4" />
                <span dir="ltr">WhatsApp: {WHATSAPP_DISPLAY}</span>
              </a>
              <div className="flex items-center gap-3 pt-2">
                {SOCIALS.map((s) => (
                  <a
                    key={s.name}
                    href={s.href}
                    target="_blank"
                    rel="noreferrer noopener"
                    aria-label={s.name}
                    title={s.name}
                    className="w-10 h-10 flex items-center justify-center rounded-xl border border-border bg-card hover:border-indigo-500 hover:text-indigo-400 text-muted-foreground transition-colors"
                  >
                    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="currentColor" aria-hidden="true">
                      <path d={s.path} />
                    </svg>
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="pt-6 flex items-center justify-center text-xs text-muted-foreground text-center">
          <div>© 2026 orga+. {t("footerAllRights")}</div>
        </div>
      </div>
    </footer>
  )
}
