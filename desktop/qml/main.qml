import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import "components"
import "views"

ApplicationWindow {
    id: window
    visible: true
    width: 1180
    height: 760
    minimumWidth: 980
    minimumHeight: 640
    title: "Bilnov Gallery • 3D Asset Platform"
    color: Theme.background

    property int activeTab: 0

    // Font Awesome Loaders
    FontLoader {
        id: faSolidLoader
        source: "../assets/fonts/fa-solid-900.ttf"
    }
    FontLoader {
        id: faRegularLoader
        source: "../assets/fonts/fa-regular-400.ttf"
    }

    // Connect toast signal from Python bridge
    Connections {
        target: Bridge
        function onToast(type, msg) {
            toastWidget.showToast(type, msg)
        }
        function onLicenseChanged() {
            if (!Bridge.isLicensed && Bridge.licenseStatusCode === "NEEDS_ACTIVATION") {
                activationDialog.open()
            }
        }
    }

    Component.onCompleted: {
        if (!Bridge.isLicensed && Bridge.licenseStatusCode === "NEEDS_ACTIVATION") {
            activationDialog.open()
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

        // Sidebar Navigation
        SidebarNav {
            id: sidebar
            Layout.preferredWidth: 230
            Layout.minimumWidth: 230
            Layout.maximumWidth: 230
            Layout.fillWidth: false
            Layout.fillHeight: true
            activeTab: window.activeTab
            onTabSelected: function(index) {
                window.activeTab = index
            }
            onOpenLicenseDialog: {
                activationDialog.open()
            }
        }

        // Main Content Area
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // Top Header Bar
            HeaderBar {
                id: header
                Layout.preferredHeight: 60
                Layout.minimumHeight: 60
                Layout.fillWidth: true
                Layout.fillHeight: false
                title: {
                    switch (window.activeTab) {
                        case 0: return I18n.t("header_gallery_title");
                        case 1: return I18n.t("header_categories_title");
                        default: return I18n.t("app_title");
                    }
                }
                subtitle: {
                    switch (window.activeTab) {
                        case 0: return I18n.t("header_gallery_subtitle");
                        case 1: return I18n.t("header_categories_subtitle");
                        default: return "";
                    }
                }
                onSearchRequested: function(query) {
                    window.activeTab = 0
                    libraryView.setSearchQuery(query)
                }
                onOpenLicenseDialog: {
                    activationDialog.open()
                }
            }

            // Views Stack
            StackLayout {
                id: viewsStack
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: window.activeTab

                LibraryView {
                    id: libraryView
                    onOpenGallery: function(images, title) {
                        lightbox.open(images, title, 0)
                    }
                }

                CategoriesView {
                    id: categoriesView
                    onSelectCategory: function(catName) {
                        window.activeTab = 0
                        libraryView.selectedCategory = catName
                        Bridge.loadLibrary(libraryView.currentSearchQuery, catName)
                    }
                }
            }
        }
    }

    // License Lockout Barrier (Task 2 & 5: Protected when license is invalid)
    Rectangle {
        id: lockOverlay
        anchors.fill: parent
        z: 99990
        color: "#F0030712"
        visible: !Bridge.isLicensed && activationDialog.opacity === 0

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 18

            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                width: 64
                height: 64
                radius: 32
                color: Qt.rgba(Theme.error.r, Theme.error.g, Theme.error.b, 0.15)
                border.color: Qt.rgba(Theme.error.r, Theme.error.g, Theme.error.b, 0.4)

                FaIcon {
                    anchors.centerIn: parent
                    icon: Icons.lock
                    size: 26
                    iconColor: Theme.error
                }
            }

            Text {
                text: Bridge.licenseStatusCode === "TRIAL_EXPIRED" ? I18n.t("status_trial_expired") : I18n.t("lock_title")
                color: "#F8FAFC"
                font.pixelSize: 18
                font.bold: true
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: Bridge.licenseMessage || I18n.t("lock_desc")
                color: "#94A3B8"
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }

            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                width: 190
                height: 40
                radius: 8
                color: activateBtnMouse.containsMouse ? Theme.primaryHover : Theme.primary

                RowLayout {
                    anchors.centerIn: parent
                    spacing: 8
                    layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight
                    FaIcon {
                        icon: Icons.key
                        size: 13
                        iconColor: "white"
                    }
                    Text {
                        text: I18n.t("btn_enter_key")
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                    }
                }

                MouseArea {
                    id: activateBtnMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: activationDialog.open()
                }
            }
        }
    }

    // Global Photo Lightbox Modal
    LightboxModal {
        id: lightbox
    }

    // Global Licensing & Activation Modal (openapi.json)
    ActivationDialog {
        id: activationDialog
    }

    // Global Toast Notification
    ToastNotification {
        id: toastWidget
    }
}
