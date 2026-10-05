import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "../components"

Item {
    id: root

    signal selectCategory(string categoryName)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        // Header info
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Text {
                text: "Local Asset Taxonomy"
                color: Theme.textPrimary
                font.pixelSize: 18
                font.bold: true
            }

            Rectangle {
                height: 24
                width: catCountText.implicitWidth + 16
                radius: 12
                color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15)
                border.color: Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.3)

                Text {
                    id: catCountText
                    anchors.centerIn: parent
                    text: Bridge.categories.length + " Categories"
                    color: Theme.primaryLight
                    font.pixelSize: 11
                    font.bold: true
                }
            }

            Item { Layout.fillWidth: true }

            Rectangle {
                width: 40
                height: 40
                radius: Theme.radiusMd
                color: Theme.surface
                border.color: Theme.border

                FaIcon {
                    anchors.centerIn: parent
                    icon: Icons.rotate
                    size: 13
                    iconColor: Theme.textPrimary
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: Bridge.loadCategories()
                }
            }
        }

        // Categories Grid
        GridView {
            id: catGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            cellWidth: Math.floor(catGrid.width / 3)
            cellHeight: 140
            model: Bridge.categories

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            delegate: Item {
                width: catGrid.cellWidth
                height: catGrid.cellHeight

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 8
                    radius: Theme.radiusMd
                    color: catItemMouse.containsMouse ? Theme.surfaceElevated : Theme.card
                    border.color: catItemMouse.containsMouse ? Theme.primary : Theme.border
                    border.width: 1

                    Behavior on color { ColorAnimation { duration: 150 } }
                    Behavior on border.color { ColorAnimation { duration: 150 } }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Rectangle {
                                width: 34
                                height: 34
                                radius: 8
                                color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15)

                                FaIcon {
                                    anchors.centerIn: parent
                                    icon: Icons.layerGroup
                                    size: 14
                                    iconColor: Theme.primaryLight
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Text {
                                    text: modelData.name || modelData.title || "Category"
                                    color: Theme.textPrimary
                                    font.pixelSize: 14
                                    font.bold: true
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }

                                Text {
                                    text: (modelData.subcategories ? modelData.subcategories.length : 0) + " Subcategories"
                                    color: Theme.textMuted
                                    font.pixelSize: 11
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }

                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "Browse assets ›"
                                color: catItemMouse.containsMouse ? Theme.primaryLight : Theme.textMuted
                                font.pixelSize: 11
                                font.bold: true
                            }
                        }
                    }

                    MouseArea {
                        id: catItemMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            var catName = modelData.name || modelData.title;
                            root.selectCategory(catName);
                        }
                    }
                }
            }
        }
    }
}
