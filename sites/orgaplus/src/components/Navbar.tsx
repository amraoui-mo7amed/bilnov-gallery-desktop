import React, { useState, useEffect } from "react"
import { useLanguage } from "@/context/LanguageContext"
import { useTheme } from "@/context/ThemeContext"
import { Button } from "@/components/ui/Button"
import { Sun, Moon, Globe, Menu, X, MessageCircle } from "lucide-react"

interface NavbarProps {
  onOpenOrderModal: () => void
}

const languages = [
  { code: "en", label: "English" },
  { code: "fr", label: "Français" },
  { code: "ar", label: "العربية" },
] as const

export const Navbar: React.FC<NavbarProps> = ({ onOpenOrderModal }) => {
  const { language, setLanguage, t, isRTL } = useLanguage()
  const { theme, toggleTheme } = useTheme()
  const [isScrolled, setIsScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [langOpen, setLangOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 20)
    window.addEventListener("scroll", onScroll)
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  const navLinks = [
    { href: "#features", label: t("navFeatures") },
    { href: "#workflows", label: t("navWorkflows") },
    { href: "#order", label: t("navHowToOrder") },
    { href: "#faq", label: t("navFaq") },
  ]

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        isScrolled || menuOpen
          ? "bg-background/90 backdrop-blur-md border-b border-border shadow-lg shadow-black/5"
          : "bg-transparent border-b border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20 gap-3">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2.5 sm:gap-3 group shrink-0">
            <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-2xl overflow-hidden shadow-md shadow-indigo-500/30 group-hover:scale-105 transition-transform">
              <img src="/icon.png" alt="orga+ logo" className="w-full h-full object-cover" />
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-xl sm:text-2xl font-black tracking-tight text-foreground">
                orga<span className="text-indigo-500">+</span>
              </span>
              <span className="text-[10px] font-medium text-muted-foreground tracking-wider uppercase">
                Asset Station
              </span>
            </div>
          </a>

          {/* Desktop nav */}
          <nav className="hidden lg:flex items-center gap-6 text-sm font-medium">
            {navLinks.map((l) => (
              <a key={l.href} href={l.href} className="text-muted-foreground hover:text-indigo-400 transition-colors">
                {l.label}
              </a>
            ))}
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="relative">
              <button
                onClick={() => setLangOpen(!langOpen)}
                className="flex items-center gap-1.5 px-3 h-10 rounded-xl text-xs font-semibold border border-border bg-card/60 hover:bg-accent transition-colors"
                aria-label="Select language"
              >
                <Globe className="w-4 h-4 text-indigo-400" />
                <span className="uppercase">{language}</span>
              </button>
              {langOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setLangOpen(false)} />
                  <div
                    className={`absolute mt-2 w-40 rounded-xl border border-border bg-card p-1.5 shadow-xl z-50 ${
                      isRTL ? "left-0" : "right-0"
                    }`}
                  >
                    {languages.map((l) => (
                      <button
                        key={l.code}
                        onClick={() => {
                          setLanguage(l.code)
                          setLangOpen(false)
                        }}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                          language === l.code
                            ? "bg-primary text-primary-foreground font-bold"
                            : "text-foreground hover:bg-accent"
                        }`}
                      >
                        <span>{l.label}</span>
                        <span className="text-[10px] opacity-75 uppercase">{l.code}</span>
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            <button
              onClick={toggleTheme}
              className="w-10 h-10 flex items-center justify-center rounded-xl border border-border bg-card/60 hover:bg-accent transition-colors"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                <Sun className="w-4 h-4 text-amber-400" />
              ) : (
                <Moon className="w-4 h-4 text-indigo-500" />
              )}
            </button>

            <Button variant="whatsapp" onClick={onOpenOrderModal} className="hidden md:inline-flex gap-2 font-bold">
              <MessageCircle className="w-4 h-4" />
              <span>{t("navOrderNow")}</span>
            </Button>

            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="lg:hidden w-10 h-10 flex items-center justify-center rounded-xl border border-border bg-card text-foreground"
              aria-label="Menu"
            >
              {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile / tablet drawer */}
      {menuOpen && (
        <div className="lg:hidden border-t border-border px-4 sm:px-6 pt-3 pb-5 space-y-3 max-h-[80vh] overflow-y-auto">
          {navLinks.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setMenuOpen(false)}
              className="block py-2.5 text-base font-medium text-muted-foreground hover:text-foreground border-b border-border/40"
            >
              {l.label}
            </a>
          ))}
          <Button
            variant="whatsapp"
            className="w-full gap-2 font-bold h-12 text-base"
            onClick={() => {
              setMenuOpen(false)
              onOpenOrderModal()
            }}
          >
            <MessageCircle className="w-5 h-5" />
            <span>{t("navOrderNow")}</span>
          </Button>
        </div>
      )}
    </header>
  )
}
