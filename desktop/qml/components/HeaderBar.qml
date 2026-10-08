import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "."

Rectangle {
    id: root
    height: 60
    implicitHeight: 60
    Layout.preferredHeight: 60
    Layout.minimumHeight: 60
    Layout.fillWidth: true
    Layout.fillHeight: false
    color: Theme.surface
    border.color: Theme.border
    border.width: 1

    property string title: I18n.t("header_gallery_title")
    property string subtitle: I18n.t("header_gallery_subtitle")

    signal searchRequested(string query)
    signal openLicense()

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        spacing: 16

        // Left Branding & Title Section
        RowLayout {
            spacing: 12
            layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

            // App Icon
            Rectangle {
                width: 36
                height: 36
                radius: Theme.radiusMd
                color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15)
                border.color: Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.3)
                border.width: 1
                clip: true

                Image {
                    anchors.centerIn: parent
                    width: 28
                    height: 28
                    source: "../../assets/icon.png"
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }
            }

            ColumnLayout {
                spacing: 2
                Text {
                    text: root.title
                    color: Theme.textPrimary
                    font.pixelSize: 16
                    font.bold: true
                }
                Text {
                    text: root.subtitle
                    color: Theme.textMuted
                    font.pixelSize: 11
                }
            }
        }

        Item {
            Layout.fillWidth: true
        }

        // Quick Search Field (filters local ./data library)
        Rectangle {
            width: 280
            height: 36
            radius: Theme.radiusMd
            color: Theme.surfaceElevated
            border.color: headerSearchInput.activeFocus ? Theme.primary : Theme.border

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 8

                FaIcon {
                    icon: Icons.search
                    size: 12
                    iconColor: Theme.textMuted
                }

                TextInput {
                    id: headerSearchInput
                    Layout.fillWidth: true
                    color: Theme.textPrimary
                    font.pixelSize: 12
                    selectByMouse: true
                    clip: true

                    Text {
                        text: I18n.t("search_placeholder")
                        color: Theme.textMuted
                        font.pixelSize: 12
                        visible: !headerSearchInput.text && !headerSearchInput.activeFocus
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                    }

                    onTextChanged: {
                        root.searchRequested(text.trim())
                    }
                }

                FaIcon {
                    icon: Icons.times
                    size: 11
                    iconColor: Theme.textMuted
                    visible: headerSearchInput.text.length > 0
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            headerSearchInput.text = ""
                            root.searchRequested("")
                        }
                    }
                }
            }
        }

        // Language Toggle Button (show English when French is active, French when English is active)
        Rectangle {
            height: 36
            Layout.minimumWidth: langRow.implicitWidth + 24
            Layout.preferredWidth: langRow.implicitWidth + 24
            radius: Theme.radiusMd
            color: langMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : Theme.surfaceElevated
            border.color: langMouse.containsMouse ? Theme.primaryLight : Theme.border
            border.width: 1

            Behavior on color { ColorAnimation { duration: 150 } }

            RowLayout {
                id: langRow
                anchors.centerIn: parent
                spacing: 6
                FaIcon {
                    icon: Icons.globe
                    size: 12
                    iconColor: Theme.primaryLight
                }
                Text {
                    text: I18n.currentLanguage === "fr" ? "English" : "Français"
                    color: Theme.textPrimary
                    font.pixelSize: 11
                    font.bold: true
                }
            }

            ToolTip.visible: langMouse.containsMouse
            ToolTip.text: I18n.currentLanguage === "fr" ? "Switch to English" : "Passer en Français"
            ToolTip.delay: 300

            MouseArea {
                id: langMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (I18n.currentLanguage === "fr") {
                        I18n.setLanguage("en")
                    } else {
                        I18n.setLanguage("fr")
                    }
                }
            }
        }

        // Open ./data Storage Directory
        Rectangle {
            Layout.minimumWidth: storageRow.implicitWidth + 24
            Layout.preferredWidth: storageRow.implicitWidth + 24
            height: 36
            radius: Theme.radiusMd
            color: storageMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : Theme.surfaceElevated
            border.color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.3)

            RowLayout {
                id: storageRow
                anchors.centerIn: parent
                spacing: 6
                FaIcon {
                    icon: Icons.folderOpen
                    size: 12
                    iconColor: Theme.primaryLight
                }
                Text {
                    text: I18n.t("open_storage_btn")
                    color: Theme.primaryLight
                    font.pixelSize: 11
                    font.bold: true
                }
            }

            MouseArea {
                id: storageMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: Bridge.openFolder("")
            }
        }

        // License Button (Green: Activated, Orange: Trial, Red: Not Activated)
        Rectangle {
            id: licenseBtn
            height: 36
            Layout.minimumWidth: licenseRow.implicitWidth + 24
            Layout.preferredWidth: licenseRow.implicitWidth + 24
            radius: Theme.radiusMd

            readonly property color statusColor: {
                if (Bridge.isLicensed && !Bridge.isTrial) return Theme.success;
                if (Bridge.isTrial) return Theme.warning;
                return Theme.error;
            }

            color: licMouse.containsMouse
                ? Qt.rgba(statusColor.r, statusColor.g, statusColor.b, 0.28)
                : Qt.rgba(statusColor.r, statusColor.g, statusColor.b, 0.15)
            border.color: statusColor
            border.width: 1

            Behavior on color { ColorAnimation { duration: 150 } }

            RowLayout {
                id: licenseRow
                anchors.centerIn: parent
                spacing: 6
                layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

                FaIcon {
                    icon: {
                        if (Bridge.isLicensed && !Bridge.isTrial) return Icons.checkCircle;
                        if (Bridge.isTrial) return Icons.clock;
                        return Icons.key;
                    }
                    size: 12
                    iconColor: licenseBtn.statusColor
                }

                Text {
                    text: {
                        if (Bridge.isLicensed && !Bridge.isTrial) return I18n.t("status_licensed");
                        if (Bridge.isTrial) return I18n.t("status_trial") + " (" + Bridge.trialDaysRemaining + "d)";
                        return I18n.t("status_activation_required");
                    }
                    color: licenseBtn.statusColor
                    font.pixelSize: 11
                    font.bold: true
                }
            }

            ToolTip.visible: licMouse.containsMouse
            ToolTip.text: I18n.t("manage_license")
            ToolTip.delay: 300

            MouseArea {
                id: licMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.openLicense()
            }
        }
    }
}
