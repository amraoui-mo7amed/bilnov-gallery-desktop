pragma Singleton
import QtQuick 2.15
import CGTips 1.0

Item {
    id: root

    property string currentLanguage: (typeof Bridge !== "undefined" && Bridge.language) ? Bridge.language : "en"
    readonly property bool isRTL: currentLanguage === "ar"

    signal languageChanged(string lang)

    Connections {
        target: (typeof Bridge !== "undefined") ? Bridge : null
        function onLanguageChanged() {
            if (typeof Bridge !== "undefined" && Bridge.language) {
                root.currentLanguage = Bridge.language;
                root.languageChanged(Bridge.language);
            }
        }
    }

    function setLanguage(lang) {
        if (lang === "en" || lang === "fr" || lang === "ar") {
            currentLanguage = lang
            languageChanged(lang)
            if (typeof Bridge !== "undefined" && Bridge.saveLanguagePreference) {
                Bridge.saveLanguagePreference(lang)
            }
        }
    }

    readonly property var translations: ({
        "en": {
            // App & Navigation
            "app_title": "Bilnov Gallery",
            "app_subtitle": "3D Asset Platform",
            "nav_gallery": "3D Asset Gallery",
            "nav_categories": "Taxonomy & Categories",
            "status_licensed": "Licensed",
            "status_trial": "Free Trial",
            "status_trial_expired": "Trial Expired",
            "status_offline": "Offline Grace",
            "status_activation_required": "Activation Required",
            "click_to_activate": "Click to activate",
            "bound_to_workstation": "Bound to Workstation",
            "days_left": "days left",
            "trial_days_left": "days trial left",

            // Header Bar
            "header_gallery_title": "3D Asset Gallery",
            "header_gallery_subtitle": "Browse models and assets in ./data",
            "header_categories_title": "Categories & Taxonomy",
            "header_categories_subtitle": "Inspect local taxonomy structure discovered in ./data",
            "search_placeholder": "Search ./data models...",
            "open_storage_btn": "Open ./data",

            // Gallery / Library View
            "filter_placeholder": "Filter models by name, category, or file...",
            "all_categories": "All Categories",
            "category_prefix": "Category: ",
            "assets_count": "Assets",
            "models_count": "Models",
            "empty_title": "No 3D Models in ./data",
            "empty_desc": "The application reads exclusively from the ./data folder.\nPlace your 3D models (.skp, .obj, .blend) and preview images inside ./data.",
            "open_folder_btn": "Open ./data Folder",

            // Categories View
            "categories_title": "Local Asset Taxonomy",
            "categories_count": "Categories",
            "subcategories_count": "Subcategories",
            "browse_assets": "Browse assets ›",

            // Model Card
            "open_location": "Open Location",
            "has_model": "3D Model",
            "no_model": "No Model",
            "imgs_count": "imgs",
            "asset_badge": "Asset",

            // Activation Dialog
            "activation_title": "Bilnov Gallery Activation",
            "activation_subtitle": "License Management & Hardware Binding",
            "device_fingerprint": "DEVICE HARDWARE FINGERPRINT (SHA-256)",
            "license_key_label": "License Key *",
            "customer_name_label": "Customer Full Name *",
            "customer_name_placeholder": "e.g. Sarah Connor",
            "email_label": "Customer Email Address *",
            "email_placeholder": "name@company.com",
            "phone_label": "Contact Phone Number *",
            "phone_placeholder": "+1 555 123 4567",
            "address_label": "Physical Address (Optional)",
            "address_placeholder": "City, Country",
            "btn_activating": "Activating with Licensing Server...",
            "btn_activate": "Activate Workstation",
            "val_key_err": "Please enter a valid License Key (min 10 characters)",
            "val_name_err": "Full Name must be at least 2 characters",
            "val_email_err": "A valid Email address is required",
            "val_phone_err": "Contact Phone must be at least 6 digits",

            // Lockout Barrier
            "lock_title": "Workstation Activation Required",
            "lock_desc": "A valid Bilnov Gallery license is required to access local 3D assets.",
            "btn_enter_key": "Enter License Key",

            // Toasts & Feedback
            "copied_toast": "Copied to clipboard!",
            "deleted_toast": "Model folder deleted from disk",
            "delete_err": "Could not delete folder",
            "lang_name_en": "English",
            "lang_name_fr": "Français",
            "lang_name_ar": "العربية"
        },
        "fr": {
            // App & Navigation
            "app_title": "Bilnov Gallery",
            "app_subtitle": "Plateforme d'actifs 3D",
            "nav_gallery": "Galerie d'actifs 3D",
            "nav_categories": "Taxonomie & Catégories",
            "status_licensed": "Sous licence",
            "status_trial": "Essai gratuit",
            "status_trial_expired": "Essai expiré",
            "status_offline": "Grâce hors-ligne",
            "status_activation_required": "Activation requise",
            "click_to_activate": "Cliquer pour activer",
            "bound_to_workstation": "Lié au poste de travail",
            "days_left": "jours restants",
            "trial_days_left": "jours d'essai restants",

            // Header Bar
            "header_gallery_title": "Galerie d'actifs 3D",
            "header_gallery_subtitle": "Parcourir les modèles et actifs dans ./data",
            "header_categories_title": "Catégories & Taxonomie",
            "header_categories_subtitle": "Inspecter la taxonomie locale découverte dans ./data",
            "search_placeholder": "Rechercher des modèles ./data...",
            "open_storage_btn": "Ouvrir ./data",

            // Gallery / Library View
            "filter_placeholder": "Filtrer par nom, catégorie ou fichier...",
            "all_categories": "Toutes les catégories",
            "category_prefix": "Catégorie : ",
            "assets_count": "Actifs",
            "models_count": "Modèles",
            "empty_title": "Aucun modèle 3D dans ./data",
            "empty_desc": "L'application lit exclusivement le dossier ./data.\nPlacez vos modèles 3D (.skp, .obj, .blend) et aperçus d'images dans ./data.",
            "open_folder_btn": "Ouvrir le dossier ./data",

            // Categories View
            "categories_title": "Taxonomie locale des actifs",
            "categories_count": "Catégories",
            "subcategories_count": "Sous-catégories",
            "browse_assets": "Parcourir les actifs ›",

            // Model Card
            "open_location": "Ouvrir l'emplacement",
            "has_model": "Modèle 3D",
            "no_model": "Aucun modèle",
            "imgs_count": "images",
            "asset_badge": "Actif",

            // Activation Dialog
            "activation_title": "Activation de Bilnov Gallery",
            "activation_subtitle": "Gestion de licence & Liaison matérielle",
            "device_fingerprint": "EMPREINTE MATÉRIELLE (SHA-256)",
            "license_key_label": "Clé de licence *",
            "customer_name_label": "Nom complet du client *",
            "customer_name_placeholder": "ex. Jean Dupont",
            "email_label": "Adresse e-mail du client *",
            "email_placeholder": "nom@entreprise.com",
            "phone_label": "Numéro de téléphone *",
            "phone_placeholder": "+33 6 12 34 56 78",
            "address_label": "Adresse physique (Optionnelle)",
            "address_placeholder": "Ville, Pays",
            "btn_activating": "Activation auprès du serveur...",
            "btn_activate": "Activer le poste de travail",
            "val_key_err": "Veuillez entrer une clé de licence valide (min 10 caractères)",
            "val_name_err": "Le nom complet doit comporter au moins 2 caractères",
            "val_email_err": "Une adresse e-mail valide est requise",
            "val_phone_err": "Le téléphone doit comporter au moins 6 chiffres",

            // Lockout Barrier
            "lock_title": "Activation du poste requise",
            "lock_desc": "Une licence Bilnov Gallery valide est requise pour accéder aux actifs 3D locaux.",
            "btn_enter_key": "Entrer la clé de licence",

            // Toasts & Feedback
            "copied_toast": "Copié dans le presse-papiers !",
            "deleted_toast": "Dossier supprimé du disque",
            "delete_err": "Impossible de supprimer le dossier",
            "lang_name_en": "English",
            "lang_name_fr": "Français",
            "lang_name_ar": "العربية"
        },
        "ar": {
            // App & Navigation
            "app_title": "معرض بيلنوف",
            "app_subtitle": "منصة الأصول ثلاثية الأبعاد",
            "nav_gallery": "معرض الأصول 3D",
            "nav_categories": "التصنيفات والتبويبات",
            "status_licensed": "مرخّص",
            "status_trial": "فترة تجريبية",
            "status_trial_expired": "انتهت التجربة",
            "status_offline": "فترة سماح دون اتصال",
            "status_activation_required": "مطلوب التفعيل",
            "click_to_activate": "انقر للتفعيل",
            "bound_to_workstation": "مرتبط بمحطة العمل",
            "days_left": "أيام متبقية",
            "trial_days_left": "أيام تجريبية متبقية",

            // Header Bar
            "header_gallery_title": "معرض الأصول ثلاثية الأبعاد",
            "header_gallery_subtitle": "تصفح النماذج والأصول المخزنة في ./data",
            "header_categories_title": "التصنيفات والتبويبات",
            "header_categories_subtitle": "استعراض تصنيفات النماذج المكتشفة في ./data",
            "search_placeholder": "بحث في نماذج ./data...",
            "open_storage_btn": "فتح ./data",

            // Gallery / Library View
            "filter_placeholder": "تصفية النماذج بالاسم أو الفئة أو الملف...",
            "all_categories": "جميع الفئات",
            "category_prefix": "الفئة: ",
            "assets_count": "أصول",
            "models_count": "نماذج",
            "empty_title": "لا توجد نماذج 3D في ./data",
            "empty_desc": "يقرأ التطبيق حصرياً من مجلد ./data.\nضع نماذجك ثلاثية الأبعاد (.skp, .obj, .blend) وصور المعاينة داخل ./data.",
            "open_folder_btn": "فتح مجلد ./data",

            // Categories View
            "categories_title": "تصنيف الأصول المحلية",
            "categories_count": "فئات",
            "subcategories_count": "فئات فرعية",
            "browse_assets": "تصفح الأصول ‹",

            // Model Card
            "open_location": "فتح المسار",
            "has_model": "نموذج 3D",
            "no_model": "بدون نموذج",
            "imgs_count": "صور",
            "asset_badge": "أصل",

            // Activation Dialog
            "activation_title": "تفعيل معرض بيلنوف",
            "activation_subtitle": "إدارة التراخيص وربط العتاد",
            "device_fingerprint": "بصمة عتاد الجهاز (SHA-256)",
            "license_key_label": "مفتاح الترخيص *",
            "customer_name_label": "الاسم الكامل للعميل *",
            "customer_name_placeholder": "مثال: محمد علي",
            "email_label": "البريد الإلكتروني للعميل *",
            "email_placeholder": "name@company.com",
            "phone_label": "رقم الهاتف للتواصل *",
            "phone_placeholder": "+966 50 123 4567",
            "address_label": "العنوان الفعلي (اختياري)",
            "address_placeholder": "المدينة، الدولة",
            "btn_activating": "جارٍ التفعيل مع خادم التراخيص...",
            "btn_activate": "تفعيل محطة العمل",
            "val_key_err": "يرجى إدخال مفتاح ترخيص صالح (10 أحرف كحد أدنى)",
            "val_name_err": "يجب أن يتكون الاسم الكامل من حرفين على الأقل",
            "val_email_err": "يلزم إدخال عنوان بريد إلكتروني صالح",
            "val_phone_err": "يجب أن يتكون رقم الهاتف من 6 أرقام على الأقل",

            // Lockout Barrier
            "lock_title": "مطلوب تفعيل محطة العمل",
            "lock_desc": "يلزم وجود ترخيص صالح لمعرض بيلنوف للوصول إلى الأصول ثلاثية الأبعاد.",
            "btn_enter_key": "إدخال مفتاح الترخيص",

            // Toasts & Feedback
            "copied_toast": "تم النسخ إلى الحافظة!",
            "deleted_toast": "تم حذف مجلد النموذج من القرص",
            "delete_err": "تعذر حذف المجلد",
            "lang_name_en": "English",
            "lang_name_fr": "Français",
            "lang_name_ar": "العربية"
        }
    })

    function t(key) {
        var dict = translations[currentLanguage];
        if (dict && dict[key] !== undefined) {
            return dict[key];
        }
        // Fallback to English
        var enDict = translations["en"];
        if (enDict && enDict[key] !== undefined) {
            return enDict[key];
        }
        return key;
    }
}
