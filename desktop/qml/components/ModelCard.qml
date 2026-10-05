import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "."

Rectangle {
    id: root
    radius: Theme.radiusMd
    color: cardMouse.containsMouse ? Theme.surfaceElevated : Theme.card
    border.color: cardMouse.containsMouse ? Theme.primary : Theme.border
    border.width: 1
    clip: true

    property var itemData: ({})
    signal openGallery(var images, string title)

    Behavior on color { ColorAnimation { duration: 150 } }
    Behavior on border.color { ColorAnimation { duration: 150 } }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // 3D Model Thumbnail
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 165
            color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.1)
            clip: true

            Image {
                id: modelThumb
                anchors.fill: parent
                fillMode: Image.PreserveAspectCrop
                source: {
                    var u = (root.itemData.first_image || (root.itemData.images_full && root.itemData.images_full.length > 0 ? root.itemData.images_full[0] : ""));
                    if (!u) return "";
                    return u;
                }
                visible: !!source && status === Image.Ready
                asynchronous: true
                smooth: true
            }

            // Fallback Icon when image not available or loading
            FaIcon {
                anchors.centerIn: parent
                visible: !modelThumb.visible
                icon: Icons.cubes
                size: 34
                iconColor: Theme.primaryLight
                opacity: 0.5
            }

            // Top Badges Row
            RowLayout {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: 8

                // Left Badge (Category / Image count)
                Rectangle {
                    width: Math.max(26, leftBadgeRow.implicitWidth + 14)
                    height: 22
                    radius: 4
                    color: "#0F172A"
                    border.color: "#334155"
                    border.width: 1
                    clip: true

                    RowLayout {
                        id: leftBadgeRow
                        anchors.centerIn: parent
                        spacing: 5
                        FaIcon {
                            icon: (root.itemData.images_count && root.itemData.images_count > 0) ? Icons.camera : Icons.tag
                            size: 9
                            iconColor: "#38BDF8"
                        }
                        Text {
                            text: {
                                if (root.itemData.images_count && root.itemData.images_count > 0) return root.itemData.images_count + " imgs";
                                if (root.itemData.category) return root.itemData.category;
                                return "Asset";
                            }
                            color: "#F8FAFC"
                            font.pixelSize: 10
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.maximumWidth: 120
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                // Right Badge (Model size / Status)
                Rectangle {
                    width: Math.max(80, rightBadgeRow.implicitWidth + 16)
                    height: 22
                    radius: 4
                    color: "#0F172A"
                    border.color: "#334155"
                    border.width: 1

                    RowLayout {
                        id: rightBadgeRow
                        anchors.centerIn: parent
                        spacing: 6
                        FaIcon {
                            icon: root.itemData.has_model ? Icons.check : Icons.cube
                            size: 9
                            iconColor: root.itemData.has_model ? "#10B981" : "#94A3B8"
                        }
                        Text {
                            text: root.itemData.model_size || (root.itemData.has_model ? "3D Model" : "No Model")
                            color: "#F8FAFC"
                            font.pixelSize: 10
                            font.bold: true
                        }
                    }
                }
            }

            // Click thumbnail to open gallery lightbox
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    var imgs = root.itemData.images_full || [];
                    root.openGallery(imgs, root.itemData.title || "");
                }
            }
        }

        // Card Content & Actions
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 12
            spacing: 8

            // Model Title
            Text {
                text: root.itemData.title || "Untitled 3D Model"
                color: Theme.textPrimary
                font.pixelSize: 12
                font.bold: true
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            // Subcategory / Category subtitle
            Text {
                text: root.itemData.category + (root.itemData.subcategory ? (" • " + root.itemData.subcategory) : "")
                color: Theme.textMuted
                font.pixelSize: 10
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Item { Layout.fillHeight: true }

            // Card Actions
            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                // PRIMARY BUTTON: Open Exact Article Location (Task 6)
                Rectangle {
                    Layout.fillWidth: true
                    height: 32
                    radius: Theme.radiusSm
                    color: openLocMouse.containsMouse ? Theme.primaryHover : Theme.primary

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6
                        FaIcon {
                            icon: Icons.folderOpen
                            size: 11
                            iconColor: "white"
                        }
                        Text {
                            text: "Open Location"
                            color: "white"
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }

                    MouseArea {
                        id: openLocMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            Bridge.openArticleLocation(root.itemData.folder_path || "");
                        }
                    }
                }

                // View Images Lightbox Button
                Rectangle {
                    visible: root.itemData.images_count && root.itemData.images_count > 0
                    width: 32
                    height: 32
                    radius: Theme.radiusSm
                    color: galleryMouse.containsMouse ? Theme.surfaceElevated : Theme.card
                    border.color: Theme.border

                    FaIcon {
                        anchors.centerIn: parent
                        icon: Icons.image
                        size: 11
                        iconColor: Theme.primaryLight
                    }

                    MouseArea {
                        id: galleryMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            var imgs = root.itemData.images_full || [];
                            root.openGallery(imgs, root.itemData.title || "");
                        }
                    }
                }

                // Copy Folder Path Button
                Rectangle {
                    id: cardCopyBtn
                    property bool isCopied: false
                    Timer {
                        id: cardCopyTimer
                        interval: 2000
                        onTriggered: cardCopyBtn.isCopied = false
                    }
                    width: 32
                    height: 32
                    radius: Theme.radiusSm
                    color: copyLocMouse.containsMouse ? Theme.surfaceElevated : Theme.card
                    border.color: cardCopyBtn.isCopied ? "#10B981" : Theme.border

                    FaIcon {
                        anchors.centerIn: parent
                        icon: cardCopyBtn.isCopied ? Icons.check : Icons.copy
                        size: 10
                        iconColor: cardCopyBtn.isCopied ? "#10B981" : Theme.textSecondary
                    }

                    MouseArea {
                        id: copyLocMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            cardCopyBtn.isCopied = true
                            cardCopyTimer.restart()
                            Bridge.copyToClipboard(root.itemData.folder_full_path || root.itemData.folder_path || "")
                        }
                    }
                }
            }
        }
    }

    MouseArea {
        id: cardMouse
        anchors.fill: parent
        hoverEnabled: true
        propagateComposedEvents: true
    }
}
