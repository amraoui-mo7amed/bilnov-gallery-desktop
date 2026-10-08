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
    property bool isSettingsActive: false

    signal searchRequested(string query)
    signal toggleSettings()
    signal backToLibrary()

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        spacing: 16

        // Left Branding & Title Section
        RowLayout {
            spacing: 12
            layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

            // Back button (when in settings) OR App icon (default library view)
            Rectangle {
                width: 36
                height: 36
                radius: Theme.radiusMd
                color: root.isSettingsActive
                    ? (backMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Theme.surfaceElevated)
                    : Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15)
                border.color: root.isSettingsActive
                    ? (backMouse.containsMouse ? Theme.primaryLight : Theme.border)
                    : Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.3)
                border.width: 1
                clip: true

                Behavior on color { ColorAnimation { duration: 150 } }

                FaIcon {
                    visible: root.isSettingsActive
                    anchors.centerIn: parent
                    icon: Icons.arrowLeft
                    size: 13
                    iconColor: backMouse.containsMouse ? "white" : Theme.primaryLight
                }

                Image {
                    visible: !root.isSettingsActive
                    anchors.centerIn: parent
                    width: 28
                    height: 28
                    source: "../../assets/icon.png"
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }

                ToolTip.visible: root.isSettingsActive && backMouse.containsMouse
                ToolTip.text: I18n.t("back_to_library")
                ToolTip.delay: 300

                MouseArea {
                    id: backMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: root.isSettingsActive ? Qt.PointingHandCursor : Qt.ArrowCursor
                    onClicked: {
                        if (root.isSettingsActive) {
                            root.backToLibrary()
                        }
                    }
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
            visible: !root.isSettingsActive
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

        // Open ./data Storage Directory
        Rectangle {
            Layout.minimumWidth: storageRow.implicitWidth + 32
            Layout.preferredWidth: storageRow.implicitWidth + 32
            Layout.maximumWidth: 210
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

        // Settings Button (Icon-Only in the Header)
        Rectangle {
            width: 36
            height: 36
            radius: Theme.radiusMd
            color: {
                if (root.isSettingsActive) return Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25);
                return settingsMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15) : Theme.surfaceElevated;
            }
            border.color: root.isSettingsActive ? Theme.primary : (settingsMouse.containsMouse ? Theme.primaryLight : Theme.border)
            border.width: 1

            Behavior on color { ColorAnimation { duration: 150 } }

            FaIcon {
                anchors.centerIn: parent
                icon: Icons.cog
                size: 14
                iconColor: root.isSettingsActive ? Theme.primaryLight : (settingsMouse.containsMouse ? Theme.textPrimary : Theme.textMuted)
            }

            ToolTip.visible: settingsMouse.containsMouse
            ToolTip.text: root.isSettingsActive ? I18n.t("back_to_library") : I18n.t("nav_settings")
            ToolTip.delay: 300

            MouseArea {
                id: settingsMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.toggleSettings()
            }
        }
    }
}
