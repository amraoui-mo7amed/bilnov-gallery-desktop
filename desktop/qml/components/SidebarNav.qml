import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "."

Rectangle {
    id: root
    width: 230
    implicitWidth: 230
    Layout.preferredWidth: 230
    Layout.minimumWidth: 230
    Layout.maximumWidth: 230
    Layout.fillWidth: false
    Layout.fillHeight: true
    color: Theme.surface
    border.color: Theme.border
    border.width: 1

    property int activeTab: 0 // 0: Gallery, 1: Categories
    signal tabSelected(int index)
    signal openLicenseDialog()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        // Logo & Title
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

            Rectangle {
                width: 38
                height: 38
                radius: Theme.radiusMd
                color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15)
                border.color: Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.3)
                clip: true

                Image {
                    anchors.centerIn: parent
                    width: 32
                    height: 32
                    source: "../../assets/icon.png"
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }
            }

            ColumnLayout {
                spacing: 2
                Text {
                    text: I18n.t("app_title")
                    color: Theme.textPrimary
                    font.pixelSize: 14
                    font.bold: true
                    horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                }
                Text {
                    text: I18n.t("app_subtitle")
                    color: Theme.textMuted
                    font.pixelSize: 10
                    horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                }
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Theme.border
        }

        // Navigation Items (Clean Gallery & Categories only; Scraper & Settings deleted)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            Repeater {
                model: [
                    { name: I18n.t("nav_gallery"), icon: Icons.cubes, index: 0 },
                    { name: I18n.t("nav_categories"), icon: Icons.layerGroup, index: 1 },
                    { name: I18n.t("nav_settings"), icon: Icons.cog, index: 2 }
                ]

                delegate: Rectangle {
                    id: navItem
                    Layout.fillWidth: true
                    height: 40
                    radius: Theme.radiusMd
                    color: {
                        if (root.activeTab === modelData.index) {
                            return Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2);
                        }
                        return navMouse.containsMouse ? Qt.rgba(1, 1, 1, 0.05) : "transparent";
                    }
                    border.color: root.activeTab === modelData.index ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.4) : "transparent"
                    border.width: 1

                    Behavior on color { ColorAnimation { duration: 150 } }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 12
                        layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

                        FaIcon {
                            icon: modelData.icon
                            size: 14
                            iconColor: root.activeTab === modelData.index ? Theme.primaryLight : (navMouse.containsMouse ? Theme.textPrimary : Theme.textSecondary)
                        }

                        Text {
                            text: modelData.name
                            color: root.activeTab === modelData.index ? Theme.primaryLight : (navMouse.containsMouse ? Theme.textPrimary : Theme.textSecondary)
                            font.pixelSize: 12
                            font.weight: root.activeTab === modelData.index ? Font.Bold : Font.Normal
                            Layout.fillWidth: true
                            horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                        }
                    }

                    MouseArea {
                        id: navMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.activeTab = modelData.index
                            root.tabSelected(modelData.index)
                        }
                    }
                }
            }
        }

        Item {
            Layout.fillHeight: true
        }
    }
}

