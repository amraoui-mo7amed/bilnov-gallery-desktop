const en = {
  // Navigation
  navFeatures: "Features",
  navWorkflows: "Workflows",
  navGallery: "Preview",
  navHowToOrder: "How to order",
  navFaq: "FAQ",
  navOrderNow: "Order on WhatsApp",

  // Hero
  heroBadge: "Asset Manager",
  heroTitlePrefix: "Organize every model and file in one place with",
  heroTitleHighlight: "orga+",
  heroTitleSuffix: "",
  heroSubtitle:
    "The desktop software for Architects, Graphic Designers & Video Makers. Browse, preview and open your library (.skp, .blend, .obj, .fbx...) instantly — fully offline, on your own PC.",
  heroCtaOrder: "Order on WhatsApp",
  heroCtaDemo: "See the preview",
  heroWindows: "Windows",
  heroTrustText: "Built for Windows PCs. Activation key delivered on WhatsApp.",

  // Jobs
  jobArchitect: "Architect",
  jobGraphiste: "Graphiste",
  jobVideoMaker: "Video Maker",

  // Workflows
  workflowsBadge: "Made for your job",
  workflowsTitle: "Tailored to Your Creative Discipline",
  workflowsSubtitle:
    "Whether you design buildings, packaging or cinematic scenes, orga+ keeps your library clean and searchable.",
  jobArchitectTitle: "Architects & Interior Designers",
  jobArchitectDesc:
    "Manage SketchUp (.skp), Revit exports, furniture, facades, doors, windows and lighting. Open the exact folder in Windows Explorer in one click.",
  jobGraphisteTitle: "Graphic & Packaging Designers",
  jobGraphisteDesc:
    "Organize product mockups, bottles, pouches and Blender (.blend) props with large multi-image previews.",
  jobVideoMakerTitle: "Video Makers & Motion Animators",
  jobVideoMakerDesc:
    "Quickly browse Cinema 4D (.c4d) projects, environments, vehicles and props ready for your render pipeline.",
  supportedFormats: "Supported formats",
  workflowOrderCta: "Order on WhatsApp",
  workflowPoint1: "Clean organized categories",
  workflowPoint2: "Instant search by name, category or file",
  workflowPoint3: "Open Location in Windows Explorer",
  workflowPoint4: "Works 100% offline",

  // Features
  featuresBadge: "Core Capabilities",
  featuresTitle: "Fast, Private and Simple",
  featuresSubtitle:
    "Everything stays on your PC. No cloud, no lag, no leaks.",
  feature1Title: "Strict Clean Structure",
  feature1Desc:
    "Category → Subcategory → Asset. A clean library with no messy subfolders or lost files.",
  feature2Title: "All Formats & Archives",
  feature2Desc:
    "SketchUp, Blender, Cinema 4D, OBJ, FBX, GLB and compressed archives (.zip, .rar, .7z).",
  feature3Title: "Hardware-Locked License",
  feature3Desc:
    "Your license is bound to your PC with a secure fingerprint and tamper protection, with a 7-day offline grace period.",
  feature4Title: "Open Location in One Click",
  feature4Desc:
    "Jump straight to the asset folder in Windows Explorer to drag your files into your workspace.",
  feature5Title: "Your Files Stay Safe",
  feature5Desc:
    "Thumbnails are cached outside your library folder so your original project files are never modified.",
  feature6Title: "Native Windows App",
  feature6Desc:
    "A fast desktop application for Windows, with English and French interface.",

  // Gallery
  galleryBadge: "Interactive Preview",
  galleryTitle: "Try the Interface",
  gallerySubtitle: "Search and filter sample asset cards like inside the app.",
  gallerySearchPlaceholder: "Search models (e.g. villa, planter, sofa, bottle)...",
  galleryAll: "All",
  galleryHasModel: "Model File",
  galleryOpenFolder: "Open Location",
  galleryEmpty: "No models match your search",
  galleryToast: "Opened in Windows Explorer:",
  galleryAngles: "angles & renders",

  // How to order
  orderBadge: "Simple ordering",
  orderTitle: "Get orga+ in 3 Easy Steps",
  orderSubtitle: "Everything happens on WhatsApp. No forms, no waiting.",
  step1Title: "Message us on WhatsApp",
  step1Desc: "Tell us your job and how many PCs you need.",
  step2Title: "We confirm your order",
  step2Desc: "We send you the price, payment details and install file.",
  step3Title: "Activate your PC",
  step3Desc: "Receive your license key and activate orga+ on your Windows PC.",

  // Modal
  modalTitle: "Order orga+",
  modalSubtitle:
    "Fill in this quick form to prepare your WhatsApp message.",
  modalNameLabel: "Your name / studio",
  modalNamePlaceholder: "e.g. Karim Architect",
  modalJobLabel: "Your job",
  modalNotesLabel: "Notes (optional)",
  modalNotesPlaceholder: "e.g. I need 3 licenses...",
  modalSubmitBtn: "Send order on WhatsApp",
  modalGuarantee: "Fast reply and activation key on WhatsApp.",

  // FAQ
  faqBadge: "Got Questions?",
  faqTitle: "Frequently Asked Questions",
  faqSubtitle: "Answers about licensing, formats and ordering.",
  faq1Q: "Which operating systems are supported?",
  faq1A: "orga+ is built for Windows.",
  faq2Q: "How does the license work?",
  faq2A:
    "Your license key is bound to your PC through a unique hardware fingerprint. It is protected against tampering and cannot be shared between computers.",
  faq3Q: "Can I use orga+ offline?",
  faq3A:
    "Yes. orga+ works on local files. After activation you get a 7-day offline grace period and the app keeps working without internet.",
  faq4Q: "Which file formats can I manage?",
  faq4A:
    "SketchUp (.skp), Blender (.blend), Cinema 4D (.c4d), OBJ, FBX, STL, GLTF/GLB and archives (.zip, .rar, .7z).",
  faq5Q: "How do I order and get my key?",
  faq5A:
    "Click 'Order on WhatsApp'. We will confirm your order and send you your activation key.",

  // Bottom CTA
  ctaTitle: "Ready to Organize Your Library?",
  ctaSubtitle:
    "Join the architects, designers and video makers who use orga+ every day.",
  ctaButton: "Chat on WhatsApp",
  ctaNote: "Fast replies for orders, activations and questions.",

  // Sticky
  stickyButton: "Order on WhatsApp",
  stickyText: "orga+ for Windows",
  stickySub: "Fast activation via WhatsApp",

  // Footer
  footerDesc:
    "orga+ is the Windows desktop software to manage, preview and open your models and assets offline.",
  footerQuickLinks: "Navigation",
  footerContact: "Order & Contact",
  footerAllRights: "All rights reserved.",
  footerDeveloper: "",
  footerWindows: "Windows only",
}

export type TranslationDict = Record<keyof typeof en, string>
export type Language = "en" | "fr" | "ar"

const fr: TranslationDict = {
  navFeatures: "Fonctionnalités",
  navWorkflows: "Métiers",
  navGallery: "Aperçu",
  navHowToOrder: "Comment commander",
  navFaq: "FAQ",
  navOrderNow: "Commander sur WhatsApp",

  heroBadge: "Gestionnaire d'actifs",
  heroTitlePrefix: "Organisez tous vos modèles et ressources au même endroit avec",
  heroTitleHighlight: "orga+",
  heroTitleSuffix: "",
  heroSubtitle:
    "Le logiciel de bureau pour Architectes, Graphistes et Vidéastes. Parcourez, prévisualisez et ouvrez votre bibliothèque (.skp, .blend, .obj, .fbx...) instantanément — 100% hors-ligne, sur votre propre PC.",
  heroCtaOrder: "Commander sur WhatsApp",
  heroCtaDemo: "Voir l'aperçu",
  heroWindows: "Windows",
  heroTrustText: "Conçu pour les PC Windows. Clé d'activation envoyée sur WhatsApp.",

  jobArchitect: "Architecte",
  jobGraphiste: "Graphiste",
  jobVideoMaker: "Vidéaste",

  workflowsBadge: "Pensé pour votre métier",
  workflowsTitle: "Adapté à votre discipline créative",
  workflowsSubtitle:
    "Que vous conceviez des bâtiments, des packagings ou des scènes cinématiques, orga+ garde votre bibliothèque propre et facile à chercher.",
  jobArchitectTitle: "Architectes & Décorateurs d'intérieur",
  jobArchitectDesc:
    "Gérez vos fichiers SketchUp (.skp), exports Revit, mobilier, façades, portes, fenêtres et luminaires. Ouvrez le dossier exact dans l'Explorateur Windows en un clic.",
  jobGraphisteTitle: "Graphistes & Designers Packaging",
  jobGraphisteDesc:
    "Classez vos mockups de produits, bouteilles, sachets et scènes Blender (.blend) avec de grands aperçus multi-images.",
  jobVideoMakerTitle: "Vidéastes & Designers Motion",
  jobVideoMakerDesc:
    "Parcourez rapidement vos projets Cinema 4D (.c4d), environnements, véhicules et accessoires prêts pour le rendu.",
  supportedFormats: "Formats pris en charge",
  workflowOrderCta: "Commander sur WhatsApp",
  workflowPoint1: "Catégories propres et bien structurées",
  workflowPoint2: "Recherche instantanée par nom, catégorie ou fichier",
  workflowPoint3: "Ouvrir l'emplacement dans l'Explorateur Windows",
  workflowPoint4: "Fonctionne 100% hors-ligne",

  featuresBadge: "Points forts",
  featuresTitle: "Rapide, privé et simple",
  featuresSubtitle:
    "Tout reste sur votre PC. Pas de cloud, pas de lenteur, pas de fuite.",
  feature1Title: "Structure stricte et propre",
  feature1Desc:
    "Catégorie → Sous-catégorie → Actif. Une bibliothèque propre, sans sous-dossiers en désordre ni fichiers perdus.",
  feature2Title: "Tous les formats et archives",
  feature2Desc:
    "SketchUp, Blender, Cinema 4D, OBJ, FBX, GLB et archives compressées (.zip, .rar, .7z).",
  feature3Title: "Licence liée au matériel",
  feature3Desc:
    "Votre licence est liée à votre PC par une empreinte sécurisée avec protection anti-falsification et 7 jours de grâce hors-ligne.",
  feature4Title: "Ouvrir l'emplacement en un clic",
  feature4Desc:
    "Accédez directement au dossier de l'actif dans l'Explorateur Windows pour glisser votre fichier dans votre logiciel de travail.",
  feature5Title: "Vos fichiers restent intacts",
  feature5Desc:
    "Les miniatures sont mises en cache hors de votre bibliothèque : vos fichiers d'origine ne sont jamais modifiés.",
  feature6Title: "Application Windows native",
  feature6Desc:
    "Une application de bureau rapide pour Windows, avec interface en anglais et en français.",

  galleryBadge: "Aperçu interactif",
  galleryTitle: "Essayez l'interface",
  gallerySubtitle: "Recherchez et filtrez des fiches d'exemple comme dans l'application.",
  gallerySearchPlaceholder: "Rechercher un modèle (ex. villa, jardinière, canapé)...",
  galleryAll: "Tous",
  galleryHasModel: "Fichier modèle",
  galleryOpenFolder: "Ouvrir l'emplacement",
  galleryEmpty: "Aucun modèle ne correspond à votre recherche",
  galleryToast: "Ouvert dans l'Explorateur Windows :",
  galleryAngles: "angles et rendus",

  orderBadge: "Commande simple",
  orderTitle: "Obtenez orga+ en 3 étapes",
  orderSubtitle: "Tout se passe sur WhatsApp. Sans formulaire, sans attente.",
  step1Title: "Écrivez-nous sur WhatsApp",
  step1Desc: "Indiquez votre métier et le nombre de PC.",
  step2Title: "Nous confirmons la commande",
  step2Desc: "Nous vous envoyons le prix, le paiement et le fichier d'installation.",
  step3Title: "Activez votre PC",
  step3Desc: "Recevez votre clé de licence et activez orga+ sur votre PC Windows.",

  modalTitle: "Commander orga+",
  modalSubtitle:
    "Remplissez ce court formulaire pour préparer votre message WhatsApp.",
  modalNameLabel: "Votre nom / studio",
  modalNamePlaceholder: "ex. Karim Architecte",
  modalJobLabel: "Votre métier",
  modalNotesLabel: "Remarques (optionnel)",
  modalNotesPlaceholder: "ex. J'ai besoin de 3 licences...",
  modalSubmitBtn: "Envoyer la commande sur WhatsApp",
  modalGuarantee: "Réponse rapide et clé d'activation sur WhatsApp.",

  faqBadge: "Des questions ?",
  faqTitle: "Questions fréquentes",
  faqSubtitle: "Réponses sur la licence, les formats et la commande.",
  faq1Q: "Quels systèmes sont pris en charge ?",
  faq1A: "orga+ est conçu pour Windows.",
  faq2Q: "Comment fonctionne la licence ?",
  faq2A:
    "Votre clé est liée à votre PC par une empreinte matérielle unique. Elle est protégée contre la falsification et ne peut pas être partagée entre ordinateurs.",
  faq3Q: "Puis-je utiliser orga+ hors-ligne ?",
  faq3A:
    "Oui. orga+ fonctionne sur des fichiers locaux. Après activation, vous avez 7 jours de grâce hors-ligne et l'application fonctionne sans Internet.",
  faq4Q: "Quels formats puis-je gérer ?",
  faq4A:
    "SketchUp (.skp), Blender (.blend), Cinema 4D (.c4d), OBJ, FBX, STL, GLTF/GLB et archives (.zip, .rar, .7z).",
  faq5Q: "Comment commander et recevoir ma clé ?",
  faq5A:
    "Cliquez sur « Commander sur WhatsApp ». Nous confirmons votre commande et vous envoyons votre clé d'activation.",

  ctaTitle: "Prêt à organiser votre bibliothèque ?",
  ctaSubtitle:
    "Rejoignez les architectes, designers et vidéastes qui utilisent orga+ chaque jour.",
  ctaButton: "Discuter sur WhatsApp",
  ctaNote: "Réponse rapide pour commandes, activations et questions.",

  stickyButton: "Commander sur WhatsApp",
  stickyText: "orga+ pour Windows",
  stickySub: "Activation rapide via WhatsApp",

  footerDesc:
    "orga+ est le logiciel Windows pour gérer, prévisualiser et ouvrir vos fichiers et modèles hors-ligne.",
  footerQuickLinks: "Navigation",
  footerContact: "Commande & Contact",
  footerAllRights: "Tous droits réservés.",
  footerDeveloper: "",
  footerWindows: "Pour Windows uniquement",
}

const ar: TranslationDict = {
  navFeatures: "المميزات",
  navWorkflows: "التخصصات",
  navGallery: "معاينة",
  navHowToOrder: "كيفية الطلب",
  navFaq: "الأسئلة الشائعة",
  navOrderNow: "اطلب عبر واتساب",

  heroBadge: "مدير الملفات والنماذج لنظام ويندوز",
  heroTitlePrefix: "نظّم جميع نماذجك وأصولك في مكان واحد مع",
  heroTitleHighlight: "orga+",
  heroTitleSuffix: "",
  heroSubtitle:
    "برنامج مكتبي للمهندسين المعماريين ومصممي الجرافيك وصناع الفيديو. تصفّح مكتبتك (.skp, .blend, .obj, .fbx...) واستعرضها وافتحها فوراً — بدون إنترنت وعلى جهازك الخاص.",
  heroCtaOrder: "اطلب عبر واتساب",
  heroCtaDemo: "شاهد المعاينة",
  heroWindows: "Windows",
  heroTrustText: "مصمم لأجهزة ويندوز. يصلك كود التفعيل عبر واتساب.",

  jobArchitect: "مهندس معماري",
  jobGraphiste: "مصمم جرافيك",
  jobVideoMaker: "صانع فيديو",

  workflowsBadge: "مصمم لمهنتك",
  workflowsTitle: "يناسب طبيعة عملك الإبداعي",
  workflowsSubtitle:
    "سواء كنت تصمم مباني أو تغليفاً أو مشاهد سينمائية، يحافظ orga+ على مكتبتك منظمة وسهلة البحث.",
  jobArchitectTitle: "المهندسون المعماريون ومصممو الديكور",
  jobArchitectDesc:
    "نظّم ملفات SketchUp (.skp) وتصاميم الأثاث والواجهات والأبواب والنوافذ والإضاءة. افتح المجلد مباشرة في مستكشف ويندوز بنقرة واحدة.",
  jobGraphisteTitle: "مصممو الجرافيك والتغليف",
  jobGraphisteDesc:
    "رتّب نماذج المنتجات والزجاجات والأكياس وملفات Blender (.blend) مع معاينة كبيرة متعددة الصور.",
  jobVideoMakerTitle: "صناع الفيديو ومصممو الحركة والموشن",
  jobVideoMakerDesc:
    "تصفح بسرعة مشاريع Cinema 4D (.c4d) والبيئات والمركبات والعناصر الجاهزة للرندر.",
  supportedFormats: "الصيغ المدعومة",
  workflowOrderCta: "اطلب عبر واتساب",
  workflowPoint1: "تصنيفات منظمة ومرتبة",
  workflowPoint2: "بحث فوري بالاسم أو القسم أو الملف",
  workflowPoint3: "فتح الموقع في مستكشف ويندوز",
  workflowPoint4: "يعمل 100% بدون إنترنت",

  featuresBadge: "المميزات الأساسية",
  featuresTitle: "سريع وخاص وبسيط",
  featuresSubtitle: "كل شيء يبقى على جهازك. بدون سحابة وبدون بطء وبدون تسريب.",
  feature1Title: "هيكلية واضحة ونظيفة",
  feature1Desc:
    "القسم ← القسم الفرعي ← العنصر. مكتبة مرتبة بدون مجلدات فوضوية أو ملفات ضائعة.",
  feature2Title: "جميع الصيغ والملفات المضغوطة",
  feature2Desc:
    "SketchUp وBlender وCinema 4D وOBJ وFBX وGLB والملفات المضغوطة (.zip, .rar, .7z).",
  feature3Title: "ترخيص مرتبط بالجهاز",
  feature3Desc:
    "يرتبط ترخيصك بجهازك ببصمة آمنة وحماية ضد التلاعب، مع فترة سماح 7 أيام بدون إنترنت.",
  feature4Title: "فتح الموقع بنقرة واحدة",
  feature4Desc:
    "انتقل مباشرة إلى مجلد العنصر في مستكشف ويندوز لسحب الملف إلى برنامج التصميم الخاص بك.",
  feature5Title: "ملفاتك في أمان",
  feature5Desc:
    "تُخزَّن الصور المصغرة خارج مجلد مكتبتك فلا يتم تعديل ملفاتك الأصلية أبداً.",
  feature6Title: "تطبيق ويندوز أصلي",
  feature6Desc:
    "تطبيق مكتبي سريع لنظام Windows بواجهة بالإنجليزية والفرنسية.",

  galleryBadge: "معاينة تفاعلية",
  galleryTitle: "جرّب الواجهة",
  gallerySubtitle: "ابحث وصفِّ بطاقات نماذج تجريبية كما داخل التطبيق.",
  gallerySearchPlaceholder: "ابحث عن نموذج (مثال: فيلا، نباتات، أريكة)...",
  galleryAll: "الكل",
  galleryHasModel: "ملف متوفر",
  galleryOpenFolder: "فتح الموقع",
  galleryEmpty: "لا توجد نماذج مطابقة لبحثك",
  galleryToast: "تم الفتح في مستكشف ويندوز:",
  galleryAngles: "زوايا ورندرات",

  orderBadge: "طلب بسيط",
  orderTitle: "احصل على orga+ في 3 خطوات",
  orderSubtitle: "كل شيء عبر واتساب. بدون نماذج وبدون انتظار.",
  step1Title: "راسلنا على واتساب",
  step1Desc: "أخبرنا بمهنتك وعدد الأجهزة المطلوبة.",
  step2Title: "نؤكد طلبك",
  step2Desc: "نرسل لك السعر وطريقة الدفع وملف التثبيت.",
  step3Title: "فعّل جهازك",
  step3Desc: "استلم كود الترخيص وفعّل orga+ على جهاز ويندوز الخاص بك.",

  modalTitle: "اطلب orga+",
  modalSubtitle:
    "املأ هذا النموذج السريع لتجهيز رسالة واتساب.",
  modalNameLabel: "اسمك / اسم الاستوديو",
  modalNamePlaceholder: "مثال: كريم المعماري",
  modalJobLabel: "مهنتك",
  modalNotesLabel: "ملاحظات (اختياري)",
  modalNotesPlaceholder: "مثال: أحتاج 3 تراخيص...",
  modalSubmitBtn: "إرسال الطلب عبر واتساب",
  modalGuarantee: "رد سريع وكود تفعيل عبر واتساب.",

  faqBadge: "لديك سؤال؟",
  faqTitle: "الأسئلة الشائعة",
  faqSubtitle: "إجابات حول الترخيص والصيغ وطريقة الطلب.",
  faq1Q: "ما هي أنظمة التشغيل المدعومة؟",
  faq1A: "تم تصميم orga+ لنظام Windows.",
  faq2Q: "كيف يعمل الترخيص؟",
  faq2A:
    "يرتبط كود الترخيص بجهازك ببصمة عتاد فريدة، وهو محمي ضد التلاعب ولا يمكن مشاركته بين أجهزة مختلفة.",
  faq3Q: "هل يعمل البرنامج بدون إنترنت؟",
  faq3A:
    "نعم. يعمل orga+ على الملفات المحلية. بعد التفعيل تحصل على 7 أيام سماح ويستمر التطبيق بالعمل بدون إنترنت.",
  faq4Q: "ما هي الصيغ التي يمكنني إدارتها؟",
  faq4A:
    "SketchUp (.skp) وBlender (.blend) وCinema 4D (.c4d) وOBJ وFBX وSTL وGLTF/GLB والأرشيف (.zip, .rar, .7z).",
  faq5Q: "كيف أطلب وأستلم الكود؟",
  faq5A:
    "اضغط على «اطلب عبر واتساب». سنؤكد طلبك ونرسل لك كود التفعيل.",

  ctaTitle: "هل أنت مستعد لتنظيم مكتبتك؟",
  ctaSubtitle:
    "انضم إلى المهندسين والمصممين وصناع الفيديو الذين يستخدمون orga+ يومياً.",
  ctaButton: "تحدث معنا على واتساب",
  ctaNote: "رد سريع للطلبات والتفعيل والاستفسارات.",

  stickyButton: "اطلب عبر واتساب",
  stickyText: "orga+ لنظام ويندوز",
  stickySub: "تفعيل سريع عبر واتساب",

  footerDesc:
    "orga+ هو برنامج ويندوز لإدارة النماذج والملفات ومعاينتها وفتحها بدون إنترنت.",
  footerQuickLinks: "التنقل",
  footerContact: "الطلب والتواصل",
  footerAllRights: "جميع الحقوق محفوظة.",
  footerDeveloper: "",
  footerWindows: "لنظام Windows فقط",
}

export const translations: Record<Language, TranslationDict> = { en, fr, ar }
