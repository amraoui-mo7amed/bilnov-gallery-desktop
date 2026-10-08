import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "../components"

Item {
    id: root
    signal openGallery(var images, string title)
    signal addItemRequested()

    property string selectedCategory: "all"
    property string currentSearchQuery: ""

    function setSearchQuery(q) {
        root.currentSearchQuery = q;
        libFilterInput.text = q;
        Bridge.loadLibrary(q, root.selectedCategory);
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 14

        // Top Filter Bar & Controls
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

            // Search filter field
            Rectangle {
                Layout.fillWidth: true
                height: 40
                radius: Theme.radiusMd
                color: Theme.surface
                border.color: libFilterInput.activeFocus ? Theme.primary : Theme.border
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 8
                    layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

                    FaIcon {
                        icon: Icons.search
                        size: 12
                        iconColor: Theme.textMuted
                    }

                    TextInput {
                        id: libFilterInput
                        Layout.fillWidth: true
                        color: Theme.textPrimary
                        font.pixelSize: 12
                        selectByMouse: true
                        clip: true
                        horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft

                        Text {
                            text: I18n.t("filter_placeholder")
                            color: Theme.textMuted
                            font.pixelSize: 12
                            visible: !libFilterInput.text && !libFilterInput.activeFocus
                            anchors.fill: parent
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                        }

                        onTextChanged: {
                            root.currentSearchQuery = text.trim();
                            Bridge.loadLibrary(text.trim(), root.selectedCategory);
                        }
                    }

                    FaIcon {
                        icon: Icons.times
                        size: 11
                        iconColor: Theme.textMuted
                        visible: libFilterInput.text.length > 0
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                libFilterInput.text = ""
                                root.currentSearchQuery = ""
                                Bridge.loadLibrary("", root.selectedCategory);
                            }
                        }
                    }
                }
            }


            // Stats info pill
            Rectangle {
                width: 130
                height: 40
                radius: Theme.radiusMd
                color: Theme.surface
                border.color: Theme.border

                RowLayout {
                    anchors.centerIn: parent
                    spacing: 6
                    layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight
                    FaIcon {
                        icon: Icons.cubes
                        size: 13
                        iconColor: Theme.primaryLight
                    }
                    Text {
                        text: Bridge.libraryTotal + " " + I18n.t("assets_count")
                        color: Theme.primaryLight
                        font.pixelSize: 12
                        font.bold: true
                    }
                }
            }

            // Add Item Button
            Rectangle {
                Layout.minimumWidth: addItemRow.implicitWidth + 32
                Layout.preferredWidth: addItemRow.implicitWidth + 32
                Layout.maximumWidth: 210
                height: 40
                radius: Theme.radiusMd
                color: addItemMouse.containsMouse ? Theme.primaryHover : Theme.primary

                RowLayout {
                    id: addItemRow
                    anchors.centerIn: parent
                    spacing: 8
                    FaIcon {
                        icon: Icons.plus
                        size: 12
                        iconColor: "white"
                    }
                    Text {
                        text: I18n.t("add_item_btn")
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                    }
                }

                MouseArea {
                    id: addItemMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.addItemRequested()
                }
            }

            // Open Folder in Finder Button
            Rectangle {
                width: 40
                height: 40
                radius: Theme.radiusMd
                color: openDirMouse.containsMouse ? Theme.surfaceElevated : Theme.surface
                border.color: Theme.border

                FaIcon {
                    anchors.centerIn: parent
                    icon: Icons.folderOpen
                    size: 13
                    iconColor: Theme.primaryLight
                }

                MouseArea {
                    id: openDirMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: Bridge.openFolder("")
                }
            }

            // Reload Button
            Rectangle {
                width: 40
                height: 40
                radius: Theme.radiusMd
                color: reloadMouse.containsMouse ? Theme.surfaceElevated : Theme.surface
                border.color: Theme.border

                FaIcon {
                    anchors.centerIn: parent
                    icon: Icons.rotate
                    size: 13
                    iconColor: Theme.textPrimary
                }

                MouseArea {
                    id: reloadMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        Bridge.loadLibrary(root.currentSearchQuery, root.selectedCategory);
                        Bridge.loadCategories();
                    }
                }
            }
        }



        // Gallery Grid / States
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            BusyIndicator {
                anchors.centerIn: parent
                running: Bridge.libraryLoading
                visible: Bridge.libraryLoading
            }

            // Empty State
            ColumnLayout {
                anchors.centerIn: parent
                visible: !Bridge.libraryLoading && Bridge.libraryItems.length === 0
                spacing: 16

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 72
                    height: 72
                    radius: 36
                    color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.1)
                    border.color: Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.25)

                    FaIcon {
                        anchors.centerIn: parent
                        icon: Icons.box
                        size: 30
                        iconColor: Theme.primaryLight
                    }
                }

                Text {
                    text: I18n.t("empty_title")
                    color: Theme.textPrimary
                    font.pixelSize: 17
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: I18n.t("empty_desc")
                    color: Theme.textMuted
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.minimumWidth: emptyOpenRow.implicitWidth + 32
                    Layout.preferredWidth: emptyOpenRow.implicitWidth + 32
                    Layout.maximumWidth: 210
                    height: 38
                    radius: Theme.radiusSm
                    color: emptyOpenMouse.containsMouse ? Theme.primaryHover : Theme.primary

                    RowLayout {
                        id: emptyOpenRow
                        anchors.centerIn: parent
                        spacing: 8
                        layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight
                        FaIcon {
                            icon: Icons.folderOpen
                            size: 12
                            iconColor: "white"
                        }
                        Text {
                            text: I18n.t("open_folder_btn")
                            color: "white"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }

                    MouseArea {
                        id: emptyOpenMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: Bridge.openFolder("")
                    }
                }
            }

            // Items Grid
            GridView {
                id: libGrid
                anchors.fill: parent
                visible: !Bridge.libraryLoading && Bridge.libraryItems.length > 0
                clip: true
                cellWidth: Math.floor(libGrid.width / 3)
                cellHeight: 310
                model: Bridge.libraryItems

                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AsNeeded
                }

                delegate: Item {
                    width: libGrid.cellWidth
                    height: libGrid.cellHeight

                    ModelCard {
                        anchors.fill: parent
                        anchors.margins: 7
                        itemData: modelData
                        onOpenGallery: root.openGallery(modelData.images_full, modelData.title)
                    }
                }
            }
        }
    }
}
