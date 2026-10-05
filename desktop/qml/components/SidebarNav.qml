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

            Rectangle {
                width: 38
                height: 38
                radius: Theme.radiusMd
                color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15)
                border.color: Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.3)

                FaIcon {
                    anchors.centerIn: parent
                    icon: Icons.cubes
                    size: 16
                    iconColor: Theme.primaryLight
                }
            }

            ColumnLayout {
                spacing: 2
                Text {
                    text: "Bilnov Gallery"
                    color: Theme.textPrimary
                    font.pixelSize: 14
                    font.bold: true
                }
                Text {
                    text: "3D Asset Platform"
                    color: Theme.textMuted
                    font.pixelSize: 10
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
                    { name: "3D Asset Gallery", icon: Icons.cubes, index: 0 },
                    { name: "Taxonomy & Categories", icon: Icons.layerGroup, index: 1 }
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

        // Licensing Lifecycle Status Pill (Task 2 OpenAPI integration)
        Rectangle {
            Layout.fillWidth: true
            height: 54
            radius: Theme.radiusMd
            color: licMouse.containsMouse ? Qt.rgba(1, 1, 1, 0.04) : Theme.surfaceElevated
            border.color: {
                if (Bridge.licenseStatusCode === "ACTIVE") return Qt.rgba(Theme.success.r, Theme.success.g, Theme.success.b, 0.4);
                if (Bridge.licenseStatusCode === "ACTIVE_OFFLINE") return Qt.rgba(Theme.warning.r, Theme.warning.g, Theme.warning.b, 0.4);
                return Qt.rgba(Theme.error.r, Theme.error.g, Theme.error.b, 0.4);
            }
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                Rectangle {
                    width: 30
                    height: 30
                    radius: 6
                    color: {
                        if (Bridge.licenseStatusCode === "ACTIVE") return Qt.rgba(Theme.success.r, Theme.success.g, Theme.success.b, 0.15);
                        if (Bridge.licenseStatusCode === "ACTIVE_OFFLINE") return Qt.rgba(Theme.warning.r, Theme.warning.g, Theme.warning.b, 0.15);
                        return Qt.rgba(Theme.error.r, Theme.error.g, Theme.error.b, 0.15);
                    }

                    FaIcon {
                        anchors.centerIn: parent
                        icon: Icons.shield
                        size: 13
                        iconColor: {
                            if (Bridge.licenseStatusCode === "ACTIVE") return Theme.success;
                            if (Bridge.licenseStatusCode === "ACTIVE_OFFLINE") return Theme.warning;
                            return Theme.error;
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1

                    Text {
                        text: {
                            if (Bridge.licenseStatusCode === "ACTIVE") return "Licensed";
                            if (Bridge.licenseStatusCode === "ACTIVE_OFFLINE") return "Offline Grace";
                            return "Activation Required";
                        }
                        color: {
                            if (Bridge.licenseStatusCode === "ACTIVE") return Theme.success;
                            if (Bridge.licenseStatusCode === "ACTIVE_OFFLINE") return Theme.warning;
                            return Theme.error;
                        }
                        font.pixelSize: 11
                        font.bold: true
                    }

                    Text {
                        text: {
                            if (Bridge.licenseStatusCode === "ACTIVE") {
                                return Bridge.customerName || "Bound to Workstation";
                            }
                            if (Bridge.licenseStatusCode === "ACTIVE_OFFLINE") {
                                return Bridge.offlineDaysRemaining + " days left";
                            }
                            return "Click to activate";
                        }
                        color: Theme.textMuted
                        font.pixelSize: 9
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                }

                FaIcon {
                    icon: Icons.chevronRight
                    size: 9
                    iconColor: Theme.textMuted
                }
            }

            MouseArea {
                id: licMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.openLicenseDialog()
            }
        }
    }
}
