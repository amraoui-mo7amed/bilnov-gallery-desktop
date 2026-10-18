import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "../components"

Item {
    id: root
    signal openGallery(var images, string title)

    property string currentSearchQuery: ""
    property string currentJob: "all"
    property string currentCategory: "all"
    property string currentSubcategory: "all"

    function effectiveCategory() {
        if (root.currentCategory && root.currentCategory !== "all") return root.currentCategory;
        if (root.currentJob && root.currentJob !== "all") {
            if (root.currentJob === "architect") return "Architect";
            if (root.currentJob === "graphiste") return "Graphiste";
            if (root.currentJob === "video maker") return "Video Maker";
            return Bridge.getJobFolder ? Bridge.getJobFolder(root.currentJob) : root.currentJob;
        }
        return "all";
    }

    function reload() {
        Bridge.loadLibrary(root.currentSearchQuery, root.effectiveCategory(), root.currentSubcategory);
    }

    function setSearchQuery(q) {
        root.currentSearchQuery = q;
        reload();
    }

    function setFilter(job, category, subcategory) {
        root.currentJob = job ? job : "all";
        root.currentCategory = category ? category : "all";
        root.currentSubcategory = subcategory ? subcategory : "all";
        reload();
    }

    Item {
        anchors.fill: parent
        anchors.margins: 20

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
        }

        // Items Grid
        GridView {
            id: libGrid
            anchors.fill: parent
            visible: !Bridge.libraryLoading && Bridge.libraryItems.length > 0
            clip: true
            cellWidth: Math.floor(libGrid.width / 3)
            cellHeight: 300
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
