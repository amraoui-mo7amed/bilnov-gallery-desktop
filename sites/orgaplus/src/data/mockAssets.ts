export type AssetKind =
  | "chair"
  | "door"
  | "lamp"
  | "bottle"
  | "pouch"
  | "scifi"
  | "car"
  | "sofa"
  | "exterior"
  | "garden"
  | "villa"

export interface Asset {
  id: string
  title: string
  job: "architect" | "graphiste" | "video_maker"
  category: string
  subcategory: string
  format: string
  size: string
  kind: AssetKind
  imageUrl: string
  imageUrls?: string[]
  depthPath: string
}

const phanThucImages = Array.from({ length: 12 }, (_, i) => `/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_${i + 1}.jpg`)

export const mockAssets: Asset[] = [
  {
    id: "villa-exterior-phan-thuc",
    title: "Modern House Exterior Villa",
    job: "architect",
    category: "Scenes",
    subcategory: "Exteriors",
    format: ".skp",
    size: "184.6 MB",
    kind: "exterior",
    imageUrl: "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_1.jpg",
    imageUrls: phanThucImages,
    depthPath: "Library\\Scenes\\Exteriors\\19492 Free Sketchup House Exterior Model",
  },
  {
    id: "garden-planter-box",
    title: "Modern Mini Garden Planter Box with Tree",
    job: "architect",
    category: "Scenes",
    subcategory: "Exteriors",
    format: ".skp",
    size: "48.2 MB",
    kind: "garden",
    imageUrl: "/feeds/Scenes/Exteriors/19885_Planter_Box/image_1.jpg",
    imageUrls: ["/feeds/Scenes/Exteriors/19885_Planter_Box/image_1.jpg"],
    depthPath: "Library\\Scenes\\Exteriors\\19885 Modern Mini Garden Planter Box",
  },
  {
    id: "villa-pool-deck",
    title: "Contemporary Luxury Villa Pool & Deck",
    job: "architect",
    category: "Scenes",
    subcategory: "Exteriors",
    format: ".skp",
    size: "184.6 MB",
    kind: "villa",
    imageUrl: "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_2.jpg",
    imageUrls: [
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_2.jpg",
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_3.jpg",
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_4.jpg",
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_1.jpg",
    ],
    depthPath: "Library\\Scenes\\Exteriors\\19492 House Exterior - Swimming Pool",
  },
  {
    id: "villa-night-lighting",
    title: "Modern Villa Architectural Night Render",
    job: "architect",
    category: "Scenes",
    subcategory: "Exteriors",
    format: ".skp",
    size: "184.6 MB",
    kind: "exterior",
    imageUrl: "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_5.jpg",
    imageUrls: [
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_5.jpg",
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_9.jpg",
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_1.jpg",
    ],
    depthPath: "Library\\Scenes\\Exteriors\\19492 House Exterior - Night Lighting",
  },
  {
    id: "villa-aerial-masterplan",
    title: "Villa Masterplan & Roof Architecture",
    job: "architect",
    category: "Scenes",
    subcategory: "Exteriors",
    format: ".skp",
    size: "184.6 MB",
    kind: "villa",
    imageUrl: "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_6.jpg",
    imageUrls: [
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_6.jpg",
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_7.jpg",
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_8.jpg",
    ],
    depthPath: "Library\\Scenes\\Exteriors\\19492 House Exterior - Aerial Overview",
  },
  {
    id: "villa-entrance-portico",
    title: "Modern Villa Entrance & Facade Portico",
    job: "architect",
    category: "Scenes",
    subcategory: "Exteriors",
    format: ".skp",
    size: "184.6 MB",
    kind: "exterior",
    imageUrl: "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_12.jpg",
    imageUrls: [
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_12.jpg",
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_11.jpg",
      "/feeds/Scenes/Exteriors/19492_House_Exterior_Phan_Thuc/image_10.jpg",
    ],
    depthPath: "Library\\Scenes\\Exteriors\\19492 House Exterior - Main Entrance",
  },
  {
    id: "cosmetic-bottle",
    title: "Amber Glass Dropper Bottle",
    job: "graphiste",
    category: "Packaging",
    subcategory: "Cosmetics",
    format: ".blend",
    size: "84.5 MB",
    kind: "bottle",
    imageUrl: "/assets/items/cosmetic-bottle.jpg",
    depthPath: "Library\\Packaging\\Cosmetics\\Amber Glass Dropper Bottle",
  },
  {
    id: "coffee-pouch",
    title: "Eco Matte Coffee Pouch 500g",
    job: "graphiste",
    category: "Branding",
    subcategory: "Bags & Pouches",
    format: ".obj",
    size: "35.1 MB",
    kind: "pouch",
    imageUrl: "/assets/items/coffee-pouch.jpg",
    depthPath: "Library\\Branding\\Bags & Pouches\\Eco Matte Coffee Pouch 500g",
  },
  {
    id: "scifi-corridor",
    title: "Cyberpunk Interior Corridor",
    job: "video_maker",
    category: "Virtual Sets",
    subcategory: "Sci-Fi",
    format: ".c4d",
    size: "340.2 MB",
    kind: "scifi",
    imageUrl: "/assets/items/scifi-corridor.jpg",
    depthPath: "Library\\Virtual Sets\\Sci-Fi\\Cyberpunk Interior Corridor",
  },
  {
    id: "sport-vehicle",
    title: "Hypercar Concept Rig",
    job: "video_maker",
    category: "Vehicles",
    subcategory: "Cars",
    format: ".fbx",
    size: "215.0 MB",
    kind: "car",
    imageUrl: "/assets/items/sport-vehicle.jpg",
    depthPath: "Library\\Vehicles\\Cars\\Hypercar Concept Rig",
  },
]
