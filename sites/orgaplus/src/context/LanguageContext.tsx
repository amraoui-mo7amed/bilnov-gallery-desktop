import React, { createContext, useContext, useEffect, useState } from "react"
import { type Language, type TranslationDict, translations } from "@/i18n/translations"

export const WHATSAPP_PHONE = "+213770555970"
export const WHATSAPP_DISPLAY = "+213 770 555 970"
export const WHATSAPP_RAW_NUMBER = "213770555970"

interface WhatsAppOrderOptions {
  job?: string
  name?: string
  notes?: string
}

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
  isRTL: boolean
  t: (key: keyof TranslationDict) => string
  getWhatsAppUrl: (options?: WhatsAppOrderOptions) => string
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem("orga_lang")
    if (saved === "en" || saved === "fr" || saved === "ar") return saved
    const navLang = navigator.language.slice(0, 2)
    if (navLang === "ar") return "ar"
    if (navLang === "en") return "en"
    return "fr"
  })

  const isRTL = language === "ar"

  useEffect(() => {
    const root = document.documentElement
    root.setAttribute("lang", language)
    root.setAttribute("dir", isRTL ? "rtl" : "ltr")
    localStorage.setItem("orga_lang", language)
  }, [language, isRTL])

  const t = (key: keyof TranslationDict): string =>
    translations[language][key] ?? translations.en[key] ?? (key as string)

  const getWhatsAppUrl = (options?: WhatsAppOrderOptions): string => {
    const { job, name, notes } = options || {}
    let message = ""

    if (language === "ar") {
      message = `مرحباً، أود طلب برنامج orga+ لنظام ويندوز.`
      if (name) message += `\n- الاسم: ${name}`
      if (job) message += `\n- المهنة: ${job}`
      if (notes) message += `\n- ملاحظات: ${notes}`
      message += `\n\nيرجى تزويدي بالسعر وخطوات التفعيل. شكراً!`
    } else if (language === "fr") {
      message = `Bonjour, je souhaite commander le logiciel orga+ pour Windows.`
      if (name) message += `\n- Nom / Studio : ${name}`
      if (job) message += `\n- Métier : ${job}`
      if (notes) message += `\n- Remarque : ${notes}`
      message += `\n\nPouvez-vous m'indiquer le prix et la procédure d'activation ? Merci !`
    } else {
      message = `Hello, I would like to order the orga+ software for Windows.`
      if (name) message += `\n- Name / Studio: ${name}`
      if (job) message += `\n- Job: ${job}`
      if (notes) message += `\n- Note: ${notes}`
      message += `\n\nPlease send me the price and activation steps. Thank you!`
    }

    return `https://wa.me/${WHATSAPP_RAW_NUMBER}?text=${encodeURIComponent(message)}`
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage: setLanguageState, isRTL, t, getWhatsAppUrl }}>
      {children}
    </LanguageContext.Provider>
  )
}

export const useLanguage = () => {
  const context = useContext(LanguageContext)
  if (!context) throw new Error("useLanguage must be used within a LanguageProvider")
  return context
}
