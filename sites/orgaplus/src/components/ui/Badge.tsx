import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary/15 text-primary border border-primary/25",
        secondary:
          "border-transparent bg-secondary/15 text-secondary border border-secondary/25",
        destructive:
          "border-transparent bg-destructive/15 text-destructive border border-destructive/25",
        outline: "text-foreground border border-border",
        success:
          "border-emerald-500/20 bg-emerald-500/15 text-emerald-400 border",
        neon:
          "border-cyan-500/30 bg-cyan-500/10 text-cyan-400 border shadow-sm shadow-cyan-500/20",
        purple:
          "border-purple-500/30 bg-purple-500/10 text-purple-400 border shadow-sm shadow-purple-500/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
