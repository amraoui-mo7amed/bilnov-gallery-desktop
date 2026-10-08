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
    title: "olga+ • 3D Asset Platform"
    color: Theme.background

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
            toastWidget.showToast(type, I18n.tMsg(msg))
        }
    }

    // Main Content Area: LibraryView is the only widget (Sidebar and SettingsView removed)
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Top Header Bar
        HeaderBar {
            id: header
            Layout.preferredHeight: 60
            Layout.minimumHeight: 60
            Layout.fillWidth: true
            Layout.fillHeight: false
            onSearchRequested: function(query) {
                libraryView.setSearchQuery(query)
            }
            onOpenLicense: {
                licenseDialog.open()
            }
        }

        // Library View is the default and only primary view
        LibraryView {
            id: libraryView
            Layout.fillWidth: true
            Layout.fillHeight: true
            onOpenGallery: function(images, title) {
                lightbox.open(images, title, 0)
            }
            onAddItemRequested: addItemDialog.open()
        }
    }

    // License Lockout Barrier (Shown only when expired/unlicensed and modal is not open)
    Rectangle {
        id: lockOverlay
        anchors.fill: parent
        z: 99990
        color: "#F0030712"
        visible: !Bridge.isLicensed && !licenseDialog.visible

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 18

            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 64
                Layout.preferredHeight: 64
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
                Layout.minimumWidth: lockBtnRow.implicitWidth + 32
                Layout.preferredWidth: lockBtnRow.implicitWidth + 32
                Layout.maximumWidth: 240
                Layout.preferredHeight: 40
                radius: 8
                color: activateBtnMouse.containsMouse ? Theme.primaryHover : Theme.primary

                RowLayout {
                    id: lockBtnRow
                    anchors.centerIn: parent
                    spacing: 8
                    FaIcon {
                        icon: Icons.key
                        size: 13
                        iconColor: "white"
                    }
                    Text {
                        text: I18n.t("license_activate_btn")
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
                    onClicked: {
                        licenseDialog.open()
                    }
                }
            }
        }
    }

    // License Management & Activation Modal (Key only + Status + Phone numbers)
    LicenseDialog {
        id: licenseDialog
    }

    // Global Photo Lightbox Modal
    LightboxModal {
        id: lightbox
    }

    // Add Item to Library Modal
    AddItemDialog {
        id: addItemDialog
    }

    // Global Toast Notification
    ToastNotification {
        id: toastWidget
    }
}
