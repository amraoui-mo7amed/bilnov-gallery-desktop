import React, { useState } from "react"
import { ThemeProvider } from "@/context/ThemeContext"
import { LanguageProvider } from "@/context/LanguageContext"
import { Navbar } from "@/components/Navbar"
import { Hero } from "@/components/Hero"
import { FeaturesSection } from "@/components/FeaturesSection"
import { BottomCta } from "@/components/BottomCta"
import { FloatingWhatsApp } from "@/components/FloatingWhatsApp"
import { StickyOrderBar } from "@/components/StickyOrderBar"
import { OrderModal } from "@/components/OrderModal"

const LandingPageContent: React.FC = () => {
  const [orderOpen, setOrderOpen] = useState(false)
  const open = () => setOrderOpen(true)

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300 overflow-x-hidden">
      <Navbar onOpenOrderModal={open} />
      <main>
        <Hero onOpenOrderModal={open} />
        <FeaturesSection />
        <BottomCta onOpenOrderModal={open} />
      </main>
      <FloatingWhatsApp onOpenOrderModal={open} />
      <StickyOrderBar onOpenOrderModal={open} />
      <OrderModal isOpen={orderOpen} onClose={() => setOrderOpen(false)} />
    </div>
  )
}

export function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <LandingPageContent />
      </LanguageProvider>
    </ThemeProvider>
  )
}

export default App
