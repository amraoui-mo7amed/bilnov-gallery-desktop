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
            "nav_gallery": "Library",
            "nav_categories": "Category",
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
            "header_gallery_subtitle": "Browse models and assets in storage",
            "header_categories_title": "Categories & Taxonomy",
            "header_categories_subtitle": "Categories discovered from the folders in storage",
            "header_settings_title": "Settings & Details",
            "header_settings_subtitle": "Manage language, workstation license and trial status",
            "search_placeholder": "Search storage models...",
            "open_storage_btn": "Open Storage",

            // Gallery / Library View
            "filter_placeholder": "Filter models by name, category, or file...",
            "all_categories": "All Categories",
            "category_prefix": "Category: ",
            "assets_count": "Assets",
            "models_count": "Models",
            "empty_title": "No 3D Models in storage",
            "empty_desc": "The application reads directly from the storage folder.\nPlace your 3D models (.skp, .obj, .blend) and preview images inside storage.",
            "open_folder_btn": "Open storage Folder",

            // Categories View
            "categories_title": "Local Asset Taxonomy",
            "categories_count": "Categories",
            "subcategories_count": "Subcategories",
            "browse_assets": "Browse assets ›",

            // Model Card
            "open_location": "Open Location",
            "add_item_btn": "Add Item",
            "add_item_title": "Add Item to Library",
            "add_item_subtitle": "Upload images, name your article and attach model files",
            "add_name_label": "Article Name",
            "add_name_placeholder": "e.g. Modern Sofa",
            "add_category_label": "Category (optional)",
            "add_category_placeholder": "My Models",
            "add_images_label": "Images",
            "add_images_hint": "The first image is the thumbnail — click ★ to change",
            "add_images_btn": "Add Images",
            "add_models_label": "Model Files",
            "add_models_btn": "Upload Model Files (any file type)",
            "thumbnail": "Thumbnail",
            "cancel": "Cancel",
            "add_save_btn": "Add to Library",
            "add_saving": "Saving...",
            "add_err_name": "Please enter an article name.",
            "add_err_images": "Please add at least one image.",
            "add_err_models": "Please upload at least one file.",
            "has_model": "3D Model",
            "no_model": "No Model",
            "imgs_count": "imgs",
            "asset_badge": "Asset",

            // Settings View
            "settings_title": "Application Settings & Details",
            "settings_subtitle": "Configure interface language, view license and customer details, and check trial status.",
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
            "section_license_title": "License Expiry Countdown",
            "section_license_desc": "Time remaining before this workstation license expires.",
            "license_refresh_btn": "Verify License",
            "license_remaining_suffix": "until expiry",
            "license_perpetual_suffix": "no expiration",
            "license_expires_on": "License expires on: ",

            "section_license_details_title": "Workstation License & Customer Details",
            "section_license_details_desc": "Current device hardware binding, licensing tier, and registered customer profile.",
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
            "activate_section_desc": "No key yet? Submit your details and we deliver the activation key to you by WhatsApp / phone. Already have a key? Use the section below.",
            "section_details_title": "Your details",
            "section_details_desc": "Required to request your license key — it is sent to you by WhatsApp / phone.",
            "section_have_key_title": "Already have a key?",
            "section_have_key_desc": "Enter your activation key to activate this workstation.",
            "activate_btn": "Activate Workstation",
            "btn_activate": "Activate",
            "btn_activating": "Activating with Licensing Server...",
            "btn_requesting": "Sending your details...",
            "register_btn": "Request License Key",
            "check_status_btn": "Check Status",
            "seg_step1": "1 · Request Key",
            "seg_step2": "2 · Activate",
            "step1_title": "Step 1 — Request your license key",
            "step1_desc": "Send your contact details. Your activation key will be delivered to you on this number by WhatsApp / phone.",
            "step2_title": "Step 2 — Activate your workstation",
            "step2_desc": "Enter the activation key you received by WhatsApp / phone.",
            "submit_details_btn": "Send Details & Request Key",
            "whatsapp_delivery_note": "Your activation key will be sent to you on this phone number via WhatsApp.",
            "link_have_key": "I already have my key →",
            "link_need_key": "← No key yet? Request one",
            "activate_flow_hint": "No key yet? Submit your details in the activation window — the activation key is sent by WhatsApp / phone.",

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
            "app_phone_value": "+213775189229",

            // Activation Dialog / Fields
            "activation_title": "Bilnov Gallery Activation",
            "activation_subtitle": "License Management & Hardware Binding",
            "device_fingerprint": "DEVICE HARDWARE FINGERPRINT (SHA-256)",
            "license_key_label": "License Key *",
            "license_key_placeholder": "BILNOV-XXXX-XXXX-XXXX",
            "customer_name_label": "Customer Full Name",
            "customer_name_placeholder": "e.g. Sarah Connor",
            "email_label": "Customer Email Address",
            "email_placeholder": "name@company.com",
            "phone_label": "Contact Phone Number",
            "phone_placeholder": "+213 555 55 55 55",
            "address_label": "Physical Address (Optional)",
            "address_placeholder": "City, Country",
            "val_key_err": "Please enter a valid License Key (min 10 characters)",
            "val_name_err": "Full Name must be at least 2 characters",
            "val_email_err": "A valid Email address is required",
            "val_phone_err": "Phone number must start with +213 (e.g. +213555555555)",

            // Lockout Barrier
            "lock_title": "Workstation Activation Required",
            "lock_desc": "A valid Bilnov Gallery license is required to access local 3D assets.",
            "btn_enter_key": "Enter License Key",

            // Toasts & Feedback
            "copied_toast": "Copied to clipboard!",
            "deleted_toast": "Model folder deleted from disk",
            "delete_err": "Could not delete folder",

            // Backend / server success & error messages
            "msg_trial_verified": "Trial status verified from server ({1}d {2}h remaining)",
            "msg_trial_local": "Trial evaluated using local clock (server unreachable)",
            "msg_activation_success": "Activation successful! Welcome, {1}.",
            "msg_activation_error": "Activation error: {1}",
            "msg_activation_failed": "Activation failed: {1}",
            "msg_activation_rejected": "Activation rejected (HTTP {1})",
            "msg_offline_active": "Offline mode active ({1} days left)",
            "msg_license_alert": "License Alert: {1}",
            "msg_registration_failed": "Registration failed: {1}",
            "msg_registration_rejected": "Registration rejected (HTTP {1})",
            "msg_status_check_failed": "Status check failed: {1}",
            "msg_status_inquiry_failed": "Status inquiry failed (HTTP {1})",
            "msg_status_label": "Status: {1}",
            "msg_added_to_library": "\"{1}\" added to your library",
            "msg_could_not_add_item": "Could not add item: {1}",
            "msg_copied": "Copied to clipboard!",
            "msg_folder_deleted": "Model folder deleted from disk",
            "msg_could_not_delete": "Could not delete folder",
            "msg_delete_error": "Delete error: {1}",
            "msg_exported": "Successfully exported {1} model(s) to {2}",
            "msg_export_failed": "Export failed: {1}",
            "msg_backup_restored": "Backup restored! {1} item metadata records updated.",
            "msg_imported": "Successfully imported {1} asset(s) into the library!",
            "msg_no_valid_assets": "No valid 3D assets or files found to import.",
            "msg_import_failed": "Import failed: {1}",
            "msg_access_denied": "Access denied: Path is outside ./data",
            "msg_folder_missing": "Folder does not exist: {1}",
            "msg_library_load_failed": "Library load failed: {1}",
            "msg_categories_load_failed": "Categories load failed: {1}",
            "msg_needs_activation": "License requires initial activation",
            "msg_license_corrupted": "License file corrupted or tampered. Activation required.",
            "msg_trial_expired": "30-Day Free Trial has expired. Workstation license required.",
            "msg_license_expired": "License expired. Online renewal required.",
            "msg_offline_expired": "7-Day Offline Grace Period has expired. Please connect to internet to verify license.",
            "msg_http_401": "Licensing server returned HTTP 401 (Unauthorized). Please contact support (+213775189229 / +213673782115).",
            "msg_server_conn": "Server connection failed: {1}",
            "msg_provide_query": "Provide an email address, phone number or device ID",
            "msg_profile_registered": "Profile registered. Wait for an administrator to generate your license key.",
            "msg_no_profile_found": "No customer profile or license found for this query",
            "msg_name_too_short": "Full Name must be at least 2 characters",
            "msg_email_required": "Valid email address is mandatory",
            "msg_phone_digits": "Contact phone number must be at least 6 digits",
            "msg_license_activated": "License activated successfully",
            "msg_license_verified": "License verified successfully",
            "msg_license_disabled": "License disabled or expired by administrator",
            "msg_heartbeat_ok": "Heartbeat verified",
            "msg_heartbeat_failed": "License validation failed on heartbeat",
            "status_code_pending": "Pending License",
            "status_code_active": "Active",
            "status_code_expired": "Expired",
            "status_code_unbound": "Unbound",
            "status_code_not_found": "Not Found",
            "status_code_ok": "OK",
            "status_code_error": "Error"
        },
        "fr": {
            // App & Navigation
            "app_title": "Bilnov Gallery",
            "app_subtitle": "Plateforme d'actifs 3D",
            "nav_gallery": "Bibliothèque",
            "nav_categories": "Catégorie",
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
            "header_gallery_subtitle": "Parcourir les modèles et actifs du stockage",
            "header_categories_title": "Catégories & Taxonomie",
            "header_categories_subtitle": "Catégories découvertes à partir des dossiers du stockage",
            "header_settings_title": "Paramètres & Détails",
            "header_settings_subtitle": "Gérer la langue, la licence et le statut d'essai",
            "search_placeholder": "Rechercher dans le stockage...",
            "open_storage_btn": "Ouvrir le stockage",

            // Gallery / Library View
            "filter_placeholder": "Filtrer par nom, catégorie ou fichier...",
            "all_categories": "Toutes les catégories",
            "category_prefix": "Catégorie : ",
            "assets_count": "Actifs",
            "models_count": "Modèles",
            "empty_title": "Aucun modèle 3D dans storage",
            "empty_desc": "L'application lit directement le dossier storage.\nPlacez vos modèles 3D (.skp, .obj, .blend) et aperçus d'images dans storage.",
            "open_folder_btn": "Ouvrir le dossier storage",

            // Categories View
            "categories_title": "Taxonomie locale des actifs",
            "categories_count": "Catégories",
            "subcategories_count": "Sous-catégories",
            "browse_assets": "Parcourir les actifs ›",

            // Model Card
            "open_location": "Ouvrir l'emplacement",
            "add_item_btn": "Ajouter",
            "add_item_title": "Ajouter un élément à la bibliothèque",
            "add_item_subtitle": "Importez des images, nommez l'article et joignez vos fichiers de modèle",
            "add_name_label": "Nom de l'article",
            "add_name_placeholder": "ex. Canapé moderne",
            "add_category_label": "Catégorie (facultatif)",
            "add_category_placeholder": "Mes modèles",
            "add_images_label": "Images",
            "add_images_hint": "La première image est la miniature — cliquez ★ pour changer",
            "add_images_btn": "Ajouter des images",
            "add_models_label": "Fichiers de modèle",
            "add_models_btn": "Importer des fichiers de modèle (tout type)",
            "thumbnail": "Miniature",
            "cancel": "Annuler",
            "add_save_btn": "Ajouter à la bibliothèque",
            "add_saving": "Enregistrement...",
            "add_err_name": "Veuillez saisir un nom d'article.",
            "add_err_images": "Veuillez ajouter au moins une image.",
            "add_err_models": "Veuillez importer au moins un fichier.",
            "has_model": "Modèle 3D",
            "no_model": "Aucun modèle",
            "imgs_count": "images",
            "asset_badge": "Actif",

            // Settings View
            "settings_title": "Paramètres & Détails de l'application",
            "settings_subtitle": "Configurer la langue, afficher la licence et les détails client, et vérifier l'essai.",
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
            "section_license_title": "Compte à rebours d'expiration",
            "section_license_desc": "Temps restant avant l'expiration de la licence de ce poste.",
            "license_refresh_btn": "Vérifier la licence",
            "license_remaining_suffix": "avant expiration",
            "license_perpetual_suffix": "sans expiration",
            "license_expires_on": "La licence prend fin le : ",

            "section_license_details_title": "Licence du poste de travail & Détails client",
            "section_license_details_desc": "Liaison matérielle de l'appareil, niveau de licence et profil client enregistré.",
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
            "activate_section_desc": "Pas encore de clé ? Envoyez vos coordonnées et nous vous livrons la clé d'activation par WhatsApp / téléphone. Vous avez déjà une clé ? Utilisez la section ci-dessous.",
            "section_details_title": "Vos coordonnées",
            "section_details_desc": "Obligatoires pour demander votre clé de licence — elle vous est envoyée par WhatsApp / téléphone.",
            "section_have_key_title": "Vous avez déjà une clé ?",
            "section_have_key_desc": "Saisissez votre clé d'activation pour activer ce poste.",
            "activate_btn": "Activer le poste de travail",
            "btn_activate": "Activer",
            "btn_activating": "Activation auprès du serveur...",
            "btn_requesting": "Envoi de vos coordonnées...",
            "register_btn": "Demander une clé de licence",
            "check_status_btn": "Vérifier le statut",
            "seg_step1": "1 · Demander la clé",
            "seg_step2": "2 · Activer",
            "step1_title": "Étape 1 — Demandez votre clé de licence",
            "step1_desc": "Envoyez vos coordonnées. Votre clé d'activation vous sera délivrée sur ce numéro par WhatsApp / téléphone.",
            "step2_title": "Étape 2 — Activez votre poste de travail",
            "step2_desc": "Saisissez la clé d'activation reçue par WhatsApp / téléphone.",
            "submit_details_btn": "Envoyer mes coordonnées et demander la clé",
            "whatsapp_delivery_note": "Votre clé d'activation vous sera envoyée sur ce numéro par WhatsApp.",
            "link_have_key": "J'ai déjà ma clé →",
            "link_need_key": "← Pas encore de clé ? En demander une",
            "activate_flow_hint": "Pas encore de clé ? Envoyez vos coordonnées dans la fenêtre d'activation — la clé est envoyée par WhatsApp / téléphone.",

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
            "app_phone_value": "+213775189229",

            // Activation Dialog / Fields
            "activation_title": "Activation de Bilnov Gallery",
            "activation_subtitle": "Gestion de licence & Liaison matérielle",
            "device_fingerprint": "EMPREINTE MATÉRIELLE (SHA-256)",
            "license_key_label": "Clé de licence *",
            "license_key_placeholder": "BILNOV-XXXX-XXXX-XXXX",
            "customer_name_label": "Nom complet du client",
            "customer_name_placeholder": "ex. Jean Dupont",
            "email_label": "Adresse e-mail du client",
            "email_placeholder": "nom@entreprise.com",
            "phone_label": "Numéro de téléphone",
            "phone_placeholder": "+213 555 55 55 55",
            "address_label": "Adresse physique (Optionnelle)",
            "address_placeholder": "Ville, Pays",
            "val_key_err": "Veuillez entrer une clé de licence valide (min 10 caractères)",
            "val_name_err": "Le nom complet doit comporter au moins 2 caractères",
            "val_email_err": "Une adresse e-mail valide est requise",
            "val_phone_err": "Le numéro doit commencer par +213 (ex. +213555555555)",

            // Lockout Barrier
            "lock_title": "Activation du poste requise",
            "lock_desc": "Une licence Bilnov Gallery valide est requise pour accéder aux actifs 3D locaux.",
            "btn_enter_key": "Entrer la clé de licence",

            // Toasts & Feedback
            "copied_toast": "Copié dans le presse-papiers !",
            "deleted_toast": "Dossier supprimé du disque",
            "delete_err": "Impossible de supprimer le dossier",

            // Backend / server success & error messages
            "msg_trial_verified": "Statut d'essai vérifié depuis le serveur ({1}j {2}h restantes)",
            "msg_trial_local": "Essai évalué avec l'horloge locale (serveur injoignable)",
            "msg_activation_success": "Activation réussie ! Bienvenue, {1}.",
            "msg_activation_error": "Erreur d'activation : {1}",
            "msg_activation_failed": "Échec de l'activation : {1}",
            "msg_activation_rejected": "Activation rejetée (HTTP {1})",
            "msg_offline_active": "Mode hors-ligne actif ({1} jours restants)",
            "msg_license_alert": "Alerte de licence : {1}",
            "msg_registration_failed": "Échec de l'enregistrement : {1}",
            "msg_registration_rejected": "Enregistrement rejeté (HTTP {1})",
            "msg_status_check_failed": "Échec de la vérification du statut : {1}",
            "msg_status_inquiry_failed": "Demande de statut échouée (HTTP {1})",
            "msg_status_label": "Statut : {1}",
            "msg_added_to_library": "« {1} » ajouté à votre bibliothèque",
            "msg_could_not_add_item": "Impossible d'ajouter l'élément : {1}",
            "msg_copied": "Copié dans le presse-papiers !",
            "msg_folder_deleted": "Dossier du modèle supprimé du disque",
            "msg_could_not_delete": "Impossible de supprimer le dossier",
            "msg_delete_error": "Erreur de suppression : {1}",
            "msg_exported": "{1} modèle(s) exporté(s) avec succès vers {2}",
            "msg_export_failed": "Échec de l'export : {1}",
            "msg_backup_restored": "Sauvegarde restaurée ! {1} fiches d'éléments mises à jour.",
            "msg_imported": "{1} ressource(s) importée(s) avec succès dans la bibliothèque !",
            "msg_no_valid_assets": "Aucun fichier ou ressource 3D valide à importer.",
            "msg_import_failed": "Échec de l'import : {1}",
            "msg_access_denied": "Accès refusé : le chemin est en dehors de ./data",
            "msg_folder_missing": "Le dossier n'existe pas : {1}",
            "msg_library_load_failed": "Échec du chargement de la bibliothèque : {1}",
            "msg_categories_load_failed": "Échec du chargement des catégories : {1}",
            "msg_needs_activation": "La licence nécessite une activation initiale",
            "msg_license_corrupted": "Fichier de licence corrompu ou modifié. Activation requise.",
            "msg_trial_expired": "L'essai gratuit de 30 jours a expiré. Licence de poste requise.",
            "msg_license_expired": "Licence expirée. Renouvellement en ligne requis.",
            "msg_offline_expired": "La période de grâce hors-ligne de 7 jours a expiré. Connectez-vous à Internet pour vérifier la licence.",
            "msg_http_401": "Le serveur de licence a renvoyé HTTP 401 (Non autorisé). Contactez le support (+213775189229 / +213673782115).",
            "msg_server_conn": "Échec de la connexion au serveur : {1}",
            "msg_provide_query": "Fournissez une adresse e-mail, un numéro de téléphone ou un ID d'appareil",
            "msg_profile_registered": "Profil enregistré. Attendez qu'un administrateur génère votre clé de licence.",
            "msg_no_profile_found": "Aucun profil client ni licence trouvé pour cette requête",
            "msg_name_too_short": "Le nom complet doit comporter au moins 2 caractères",
            "msg_email_required": "Une adresse e-mail valide est obligatoire",
            "msg_phone_digits": "Le numéro de téléphone doit comporter au moins 6 chiffres",
            "msg_license_activated": "Licence activée avec succès",
            "msg_license_verified": "Licence vérifiée avec succès",
            "msg_license_disabled": "Licence désactivée ou expirée par l'administrateur",
            "msg_heartbeat_ok": "Heartbeat vérifié",
            "msg_heartbeat_failed": "Échec de la validation de la licence lors du heartbeat",
            "status_code_pending": "Clé en attente",
            "status_code_active": "Active",
            "status_code_expired": "Expirée",
            "status_code_unbound": "Non lié",
            "status_code_not_found": "Introuvable",
            "status_code_ok": "OK",
            "status_code_error": "Erreur"
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

    // Maps exact English messages coming from the backend/server to i18n keys
    readonly property var msgExact: ({
        "Trial evaluated using local clock (server unreachable)": "msg_trial_local",
        "Copied to clipboard!": "msg_copied",
        "Model folder deleted from disk": "msg_folder_deleted",
        "Could not delete folder": "msg_could_not_delete",
        "No valid 3D assets or files found to import.": "msg_no_valid_assets",
        "Access denied: Path is outside ./data": "msg_access_denied",
        "License requires initial activation": "msg_needs_activation",
        "License file corrupted or tampered. Activation required.": "msg_license_corrupted",
        "30-Day Free Trial has expired. Workstation license required.": "msg_trial_expired",
        "License expired. Online renewal required.": "msg_license_expired",
        "7-Day Offline Grace Period has expired. Please connect to internet to verify license.": "msg_offline_expired",
        "Licensing server returned HTTP 401 (Unauthorized). Please contact support (+213775189229 / +213673782115).": "msg_http_401",
        "Provide an email address, phone number or device ID": "msg_provide_query",
        "No customer profile or license found for this query": "msg_no_profile_found",
        "At least one model file is required": "add_err_models",
        "Profile registered. Wait for an administrator to generate your license key.": "msg_profile_registered",
        "Profile registered. Waiting for an administrator to generate the license key.": "msg_profile_registered",
        "Full Name must be at least 2 characters": "msg_name_too_short",
        "Valid email address is mandatory": "msg_email_required",
        "Contact phone number must be at least 6 digits": "msg_phone_digits",
        "License activated successfully": "msg_license_activated",
        "License successfully activated!": "msg_license_activated",
        "License verified successfully": "msg_license_verified",
        "License disabled or expired by administrator": "msg_license_disabled",
        "Heartbeat verified": "msg_heartbeat_ok",
        "License validation failed on heartbeat": "msg_heartbeat_failed",
        "PENDING_LICENSE": "status_code_pending",
        "ACTIVE": "status_code_active",
        "EXPIRED": "status_code_expired",
        "UNBOUND": "status_code_unbound",
        "NOT_FOUND": "status_code_not_found",
        "OK": "status_code_ok",
        "ERROR": "status_code_error",
        "TRIAL": "status_trial",
        "NEEDS_ACTIVATION": "status_activation_required",
        "TRIAL_EXPIRED": "status_trial_expired",
        "OFFLINE_EXPIRED": "status_offline"
    })

    // Matches parameterised English messages; {1}, {2}... are filled from the
    // captured groups. Groups listed in "rec" are translated recursively.
    readonly property var msgRules: ([
        { re: /^Trial status verified from server \((\d+)d (\d+)h remaining\)$/, k: "msg_trial_verified", rec: [] },
        { re: /^Activation successful! Welcome,\s*(.+?)\.?$/, k: "msg_activation_success", rec: [] },
        { re: /^Activation error:\s*(.*)$/, k: "msg_activation_error", rec: [1] },
        { re: /^Activation failed:\s*(.*)$/, k: "msg_activation_failed", rec: [1] },
        { re: /^Offline mode active \((\d+) days left\)$/, k: "msg_offline_active", rec: [] },
        { re: /^License Alert:\s*(.*)$/, k: "msg_license_alert", rec: [1] },
        { re: /^Registration failed:\s*(.*)$/, k: "msg_registration_failed", rec: [1] },
        { re: /^Status check failed:\s*(.*)$/, k: "msg_status_check_failed", rec: [1] },
        { re: /^"(.+)" added to your library$/, k: "msg_added_to_library", rec: [] },
        { re: /^Could not add item:\s*(.*)$/, k: "msg_could_not_add_item", rec: [1] },
        { re: /^Delete error:\s*(.*)$/, k: "msg_delete_error", rec: [1] },
        { re: /^Successfully exported (\d+) models? to (.+)$/, k: "msg_exported", rec: [] },
        { re: /^Export failed:\s*(.*)$/, k: "msg_export_failed", rec: [1] },
        { re: /^Backup restored! (\d+) item metadata records updated\.$/, k: "msg_backup_restored", rec: [] },
        { re: /^Successfully imported (\d+) asset\(s\) into the library!$/, k: "msg_imported", rec: [] },
        { re: /^Import failed:\s*(.*)$/, k: "msg_import_failed", rec: [1] },
        { re: /^Folder does not exist:\s*(.*)$/, k: "msg_folder_missing", rec: [] },
        { re: /^Library load failed:\s*(.*)$/, k: "msg_library_load_failed", rec: [1] },
        { re: /^Categories load failed:\s*(.*)$/, k: "msg_categories_load_failed", rec: [1] },
        { re: /^Server connection failed:\s*(.*)$/, k: "msg_server_conn", rec: [1] },
        { re: /^Activation rejected \(HTTP (\d+)\)$/, k: "msg_activation_rejected", rec: [] },
        { re: /^Status inquiry failed \(HTTP (\d+)\)$/, k: "msg_status_inquiry_failed", rec: [] },
        { re: /^Registration rejected \(HTTP (\d+)\)$/, k: "msg_registration_rejected", rec: [] },
        { re: /^Status: (.+)$/, k: "msg_status_label", rec: [1] }
    ])

    function tMsg(text) {
        if (text === undefined || text === null || text === "") return "";
        var s = String(text);
        var exact = msgExact[s];
        if (exact !== undefined) return t(exact);
        for (var i = 0; i < msgRules.length; i++) {
            var rule = msgRules[i];
            var m = s.match(rule.re);
            if (!m) continue;
            var out = t(rule.k);
            for (var g = 1; g < m.length; g++) {
                var v = (m[g] === undefined) ? "" : m[g];
                if (rule.rec && rule.rec.indexOf(g) !== -1) v = tMsg(v);
                out = out.replace("{" + g + "}", v);
            }
            return out;
        }
        return s;
    }
}
