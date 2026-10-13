import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "."

Rectangle {
    id: root
    radius: Theme.radiusMd
    color: Theme.card
    border.color: cardHover.containsMouse ? Theme.primary : Theme.border
    border.width: 1
    clip: true

    property var itemData: ({})
    signal openGallery(var images, string title)

    Behavior on border.color { ColorAnimation { duration: 150 } }

    function coverSource() {
        var u = (root.itemData.first_image || (root.itemData.images_full && root.itemData.images_full.length > 0 ? root.itemData.images_full[0] : ""));
        return u || "";
    }

    // Full-bleed cover image
    Image {
        id: cover
        anchors.fill: parent
        fillMode: Image.PreserveAspectCrop
        source: root.coverSource()
        visible: !!source && status === Image.Ready
        asynchronous: true
        smooth: true
        mipmap: true
    }

    // Fallback background + icon when no image is available
    Rectangle {
        anchors.fill: parent
        visible: !cover.visible
        color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.1)

        FaIcon {
            anchors.centerIn: parent
            icon: Icons.cubes
            size: 38
            iconColor: Theme.primaryLight
            opacity: 0.5
        }
    }

    // Click anywhere on the card to open the gallery
    MouseArea {
        id: cardHover
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            var imgs = root.itemData.images_full || [];
            root.openGallery(imgs, root.itemData.title || "");
        }
    }

    // Bottom action bar (icon-only buttons)
    RowLayout {
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8
        layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

        // Open exact article location
        Rectangle {
            width: 32
            height: 32
            radius: 16
            color: openLocMouse.containsMouse ? Theme.primary : "#B30A0E1A"
            border.color: "#33FFFFFF"

            FaIcon {
                anchors.centerIn: parent
                icon: Icons.folderOpen
                size: 12
                iconColor: openLocMouse.containsMouse ? "white" : Theme.primaryLight
            }

            ToolTip.visible: openLocMouse.containsMouse
            ToolTip.text: I18n.t("open_location")
            ToolTip.delay: 300

            MouseArea {
                id: openLocMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: Bridge.openArticleLocation(root.itemData.folder_path || "")
            }
        }

        // Copy folder path
        Rectangle {
            id: copyBtn
            property bool isCopied: false
            Timer {
                id: copyTimer
                interval: 2000
                onTriggered: copyBtn.isCopied = false
            }
            width: 32
            height: 32
            radius: 16
            color: copyMouse.containsMouse ? Theme.primary : "#B30A0E1A"
            border.color: copyBtn.isCopied ? Theme.success : "#33FFFFFF"

            FaIcon {
                anchors.centerIn: parent
                icon: copyBtn.isCopied ? Icons.check : Icons.copy
                size: 11
                iconColor: copyBtn.isCopied ? Theme.success : Theme.primaryLight
            }

            ToolTip.visible: copyMouse.containsMouse
            ToolTip.text: I18n.t("open_location")
            ToolTip.delay: 300

            MouseArea {
                id: copyMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    copyBtn.isCopied = true;
                    copyTimer.restart();
                    Bridge.copyToClipboard(root.itemData.folder_full_path || root.itemData.folder_path || "");
                }
            }
        }
    }
}
