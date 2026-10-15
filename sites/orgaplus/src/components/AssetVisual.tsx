import React, { useState } from "react"
import {
  Armchair,
  DoorOpen,
  Lamp,
  FlaskConical,
  ShoppingBag,
  Clapperboard,
  Car,
  Sofa,
  Building2,
  Trees,
  Castle,
} from "lucide-react"
import type { AssetKind } from "@/data/mockAssets"
import { cn } from "@/lib/utils"

const kinds: Record<
  AssetKind,
  { icon: React.ElementType; gradient: string; glow: string }
> = {
  chair: { icon: Armchair, gradient: "from-indigo-600/50 via-indigo-900/60 to-[#0A0E1A]", glow: "bg-indigo-400/40" },
  door: { icon: DoorOpen, gradient: "from-sky-600/50 via-blue-900/60 to-[#0A0E1A]", glow: "bg-sky-400/40" },
  lamp: { icon: Lamp, gradient: "from-amber-500/40 via-orange-900/50 to-[#0A0E1A]", glow: "bg-amber-400/40" },
  sofa: { icon: Sofa, gradient: "from-violet-600/50 via-purple-900/60 to-[#0A0E1A]", glow: "bg-violet-400/40" },
  bottle: { icon: FlaskConical, gradient: "from-fuchsia-600/50 via-purple-900/60 to-[#0A0E1A]", glow: "bg-fuchsia-400/40" },
  pouch: { icon: ShoppingBag, gradient: "from-pink-600/45 via-rose-900/55 to-[#0A0E1A]", glow: "bg-pink-400/40" },
  scifi: { icon: Clapperboard, gradient: "from-cyan-500/45 via-teal-900/60 to-[#0A0E1A]", glow: "bg-cyan-400/40" },
  car: { icon: Car, gradient: "from-emerald-500/40 via-teal-900/60 to-[#0A0E1A]", glow: "bg-emerald-400/40" },
  exterior: { icon: Building2, gradient: "from-sky-600/50 via-indigo-900/60 to-[#0A0E1A]", glow: "bg-sky-400/40" },
  garden: { icon: Trees, gradient: "from-emerald-600/50 via-teal-900/60 to-[#0A0E1A]", glow: "bg-emerald-400/40" },
  villa: { icon: Castle, gradient: "from-indigo-600/50 via-blue-900/60 to-[#0A0E1A]", glow: "bg-indigo-400/40" },
}

export interface AssetVisualProps {
  kind: AssetKind
  imageUrl?: string
  alt?: string
  className?: string
  iconClassName?: string
}

/** High-fidelity real image renderer with smooth fallback to vector card. */
export const AssetVisual: React.FC<AssetVisualProps> = ({
  kind,
  imageUrl,
  alt = "",
  className,
  iconClassName,
}) => {
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)
  const { icon: Icon, gradient, glow } = kinds[kind]

  const showImage = Boolean(imageUrl && !error)

  return (
    <div
      className={cn(
        "relative w-full h-full overflow-hidden flex items-center justify-center bg-[#0A0E1A]",
        className
      )}
    >
      {/* Fallback / Loading vector card */}
      {(!showImage || !loaded) && (
        <div
          className={cn(
            "absolute inset-0 bg-gradient-to-br flex items-center justify-center transition-opacity duration-300",
            gradient
          )}
        >
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff0f_1px,transparent_1px),linear-gradient(to_bottom,#ffffff0f_1px,transparent_1px)] bg-[size:20px_20px]" />
          <div className={cn("absolute w-1/2 aspect-square rounded-full blur-2xl", glow)} />
          <Icon
            className={cn(
              "relative w-1/3 h-1/3 min-w-8 min-h-8 text-white/80 drop-shadow-[0_4px_12px_rgba(0,0,0,0.6)]",
              iconClassName
            )}
            strokeWidth={1.4}
          />
        </div>
      )}

      {/* Real Image */}
      {showImage && (
        <>
          <img
            src={imageUrl}
            alt={alt}
            loading="lazy"
            decoding="async"
            onLoad={() => setLoaded(true)}
            onError={() => setError(true)}
            className={cn(
              "w-full h-full object-cover object-center transition-all duration-500",
              loaded ? "opacity-100 scale-100" : "opacity-0 scale-105"
            )}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20 pointer-events-none" />
        </>
      )}
    </div>
  )
}
