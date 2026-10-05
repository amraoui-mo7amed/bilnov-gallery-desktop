pragma Singleton
import QtQuick 2.15
import CGTips 1.0

Item {
    id: root

    property string currentLanguage: (typeof Bridge !== "undefined" && Bridge.language) ? Bridge.language : "en"
    readonly property bool isRTL: false

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
        if (lang === "en" || lang === "fr") {
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
            "nav_settings": "Settings & Details",
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
            "header_settings_title": "Settings & Details",
            "header_settings_subtitle": "Manage language, workstation license, trial status, and data backup",
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

            // Settings View
            "settings_title": "Application Settings & Details",
            "settings_subtitle": "Configure interface language, view license and customer details, check trial status, and import/export data.",
            "section_language_title": "Language / Langue",
            "section_language_desc": "Select your preferred application display language (EN / FR only).",
            "lang_name_en": "English",
            "lang_name_fr": "Français",

            "section_trial_title": "Free Trial Countdown",
            "section_trial_desc": "Evaluated and verified through secure network server time.",
            "trial_active_badge": "Trial Active",
            "trial_expired_badge": "Trial Ended",
            "trial_remaining_suffix": "remaining",
            "trial_net_verified": "Verified with licensing server time",
            "trial_local_verified": "Evaluated with local clock (offline)",
            "trial_expires_on": "Trial expires on: ",
            "trial_refresh_btn": "Verify Network Time",

            "section_license_title": "Workstation License & Customer Details",
            "section_license_desc": "Current device hardware binding, licensing tier, and registered customer profile.",
            "field_device_id": "Hardware Device Fingerprint (SHA-256)",
            "field_license_key": "License Key",
            "field_license_status": "Status",
            "field_customer_name": "Customer Name",
            "field_customer_email": "Customer Email",
            "field_customer_phone": "Customer Phone",
            "field_expires_at": "License Expiration",
            "btn_copy": "Copy",
            "btn_copied": "Copied!",

            "activate_section_title": "Activate or Change License",
            "activate_section_desc": "Enter your official Bilnov Gallery workstation key to remove trial limits.",
            "activate_btn": "Activate Workstation",
            "btn_activating": "Activating with Licensing Server...",

            "section_backup_title": "Library Data & Asset Import",
            "section_backup_desc": "Export your library metadata backup, or import 3D models and archives into your local gallery.",
            "export_backup_btn": "Export Library Backup (.json)",
            "export_backup_desc": "Saves all model metadata, taxonomy categories, user preferences, and license status to a portable JSON file.",
            "import_backup_btn": "Import Files to Library",
            "import_backup_desc": "Import 3D model files (.skp, .obj, .fbx, .blend, .glb, .stl, etc.), archives (.zip), or JSON backups into your gallery library.",
            "import_folder_btn": "Import Asset Folder",

            "section_app_info_title": "Application Information",
            "app_name_label": "Application",
            "app_version_label": "Version",
            "app_developer_label": "Developed by",
            "app_developer_value": "Bilnov",
            "app_phone_label": "Phone / Contact",
            "app_phone_value": "+213776139475",

            // Activation Dialog / Fields
            "activation_title": "Bilnov Gallery Activation",
            "activation_subtitle": "License Management & Hardware Binding",
            "device_fingerprint": "DEVICE HARDWARE FINGERPRINT (SHA-256)",
            "license_key_label": "License Key *",
            "license_key_placeholder": "BILNOV-XXXX-XXXX-XXXX",
            "customer_name_label": "Customer Full Name *",
            "customer_name_placeholder": "e.g. Sarah Connor",
            "email_label": "Customer Email Address *",
            "email_placeholder": "name@company.com",
            "phone_label": "Contact Phone Number *",
            "phone_placeholder": "+1 555 123 4567",
            "address_label": "Physical Address (Optional)",
            "address_placeholder": "City, Country",
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
            "delete_err": "Could not delete folder"
        },
        "fr": {
            // App & Navigation
            "app_title": "Bilnov Gallery",
            "app_subtitle": "Plateforme d'actifs 3D",
            "nav_gallery": "Galerie d'actifs 3D",
            "nav_categories": "Taxonomie & Catégories",
            "nav_settings": "Paramètres & Détails",
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
            "header_settings_title": "Paramètres & Détails",
            "header_settings_subtitle": "Gérer la langue, la licence, le statut d'essai et la sauvegarde",
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

            // Settings View
            "settings_title": "Paramètres & Détails de l'application",
            "settings_subtitle": "Configurer la langue, afficher la licence et les détails client, vérifier l'essai et gérer les sauvegardes.",
            "section_language_title": "Langue de l'interface",
            "section_language_desc": "Choisissez votre langue d'affichage préférée (EN / FR uniquement).",
            "lang_name_en": "English",
            "lang_name_fr": "Français",

            "section_trial_title": "Compte à rebours de l'essai gratuit",
            "section_trial_desc": "Évalué et vérifié avec l'heure exacte du serveur réseau.",
            "trial_active_badge": "Essai actif",
            "trial_expired_badge": "Essai terminé",
            "trial_remaining_suffix": "restants",
            "trial_net_verified": "Vérifié avec l'heure du serveur de licence",
            "trial_local_verified": "Évalué avec l'horloge locale (hors-ligne)",
            "trial_expires_on": "L'essai prend fin le : ",
            "trial_refresh_btn": "Vérifier l'heure réseau",

            "section_license_title": "Licence du poste de travail & Détails client",
            "section_license_desc": "Liaison matérielle de l'appareil, niveau de licence et profil client enregistré.",
            "field_device_id": "Empreinte matérielle de l'appareil (SHA-256)",
            "field_license_key": "Clé de licence",
            "field_license_status": "Statut",
            "field_customer_name": "Nom du client",
            "field_customer_email": "E-mail du client",
            "field_customer_phone": "Téléphone du client",
            "field_expires_at": "Expiration de la licence",
            "btn_copy": "Copier",
            "btn_copied": "Copié !",

            "activate_section_title": "Activer ou changer de licence",
            "activate_section_desc": "Entrez votre clé officielle Bilnov Gallery pour supprimer les limites de l'essai.",
            "activate_btn": "Activer le poste de travail",
            "btn_activating": "Activation auprès du serveur...",

            "section_backup_title": "Gestion des données & Importation d'actifs",
            "section_backup_desc": "Exportez la sauvegarde de votre bibliothèque ou importez des modèles 3D et archives.",
            "export_backup_btn": "Exporter la sauvegarde (.json)",
            "export_backup_desc": "Enregistre toutes les métadonnées de modèles, catégories, préférences et statut de licence dans un fichier JSON.",
            "import_backup_btn": "Importer des fichiers dans la bibliothèque",
            "import_backup_desc": "Importez des fichiers 3D (.skp, .obj, .fbx, .blend, .glb, .stl, etc.), archives (.zip) ou sauvegardes JSON dans votre bibliothèque locale.",
            "import_folder_btn": "Importer un dossier d'actifs",

            "section_app_info_title": "Informations sur l'application",
            "app_name_label": "Application",
            "app_version_label": "Version",
            "app_developer_label": "Développé par",
            "app_developer_value": "Bilnov",
            "app_phone_label": "Téléphone / Contact",
            "app_phone_value": "+213776139475",

            // Activation Dialog / Fields
            "activation_title": "Activation de Bilnov Gallery",
            "activation_subtitle": "Gestion de licence & Liaison matérielle",
            "device_fingerprint": "EMPREINTE MATÉRIELLE (SHA-256)",
            "license_key_label": "Clé de licence *",
            "license_key_placeholder": "BILNOV-XXXX-XXXX-XXXX",
            "customer_name_label": "Nom complet du client *",
            "customer_name_placeholder": "ex. Jean Dupont",
            "email_label": "Adresse e-mail du client *",
            "email_placeholder": "nom@entreprise.com",
            "phone_label": "Numéro de téléphone *",
            "phone_placeholder": "+33 6 12 34 56 78",
            "address_label": "Adresse physique (Optionnelle)",
            "address_placeholder": "Ville, Pays",
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
            "delete_err": "Impossible de supprimer le dossier"
        }
    })

    function t(key) {
        var dict = translations[currentLanguage];
        if (dict && dict[key] !== undefined) {
            return dict[key];
        }
        var enDict = translations["en"];
        if (enDict && enDict[key] !== undefined) {
            return enDict[key];
        }
        return key;
    }
}
