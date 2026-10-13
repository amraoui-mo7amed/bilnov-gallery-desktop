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

    // Active filter state (job = top level folder, category = library category, subcategory)
    property string jobFilter: "all"
    property string categoryFilter: "all"
    property string subcategoryFilter: "all"

    signal searchRequested(string query)
    signal openLicense()
    signal addItemRequested()
    signal filterChanged(string job, string category, string subcategory)

    function jobDisplay(id) {
        if (id === "architect") return I18n.t("job_architect");
        if (id === "graphiste") return I18n.t("job_graphiste");
        if (id === "video maker") return I18n.t("job_video_maker");
        return I18n.t("all_jobs");
    }

    function categoryOptions() {
        var arr = [{ name: "all", label: I18n.t("all_categories") }];
        var cats = Bridge.categories || [];
        for (var i = 0; i < cats.length; i++) {
            var n = cats[i].name || cats[i].title || "";
            if (n) arr.push({ name: n, label: n });
        }
        return arr;
    }

    function emitFilter() {
        root.filterChanged(root.jobFilter, root.categoryFilter, root.subcategoryFilter);
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        spacing: 12

        // App Icon + Wordmark
        RowLayout {
            spacing: 10
            layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

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

            Text {
                text: I18n.t("app_title")
                color: Theme.textPrimary
                font.pixelSize: 17
                font.bold: true
            }
        }

        Item { Layout.fillWidth: true }

        // Search Field
        Rectangle {
            id: searchBox
            Layout.fillWidth: true
            Layout.maximumWidth: 420
            Layout.minimumWidth: 200
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

                    onTextChanged: root.searchRequested(text.trim())
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

        // Filter Button (icon only)
        Rectangle {
            id: filterBtn
            width: 36
            height: 36
            radius: Theme.radiusMd
            color: {
                if (filterPopup.visible) return Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.3);
                return filterMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : Theme.surfaceElevated;
            }
            border.color: filterBtn.hasActiveFilter ? Theme.primary : (filterMouse.containsMouse ? Theme.primaryLight : Theme.border)
            border.width: 1

            readonly property bool hasActiveFilter: root.jobFilter !== "all" || root.categoryFilter !== "all" || root.subcategoryFilter !== "all"

            FaIcon {
                anchors.centerIn: parent
                icon: Icons.filter
                size: 14
                iconColor: filterBtn.hasActiveFilter ? Theme.primaryLight : Theme.textPrimary
            }

            MouseArea {
                id: filterMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (filterPopup.visible) filterPopup.close();
                    else filterPopup.open();
                }
            }

            ToolTip.visible: filterMouse.containsMouse && !filterPopup.visible
            ToolTip.text: I18n.t("filter_title")
            ToolTip.delay: 300
        }

        // Language Toggle (text only: EN / FR)
        Rectangle {
            id: langBtn
            width: 46
            height: 36
            radius: Theme.radiusMd
            color: langMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : Theme.surfaceElevated
            border.color: langMouse.containsMouse ? Theme.primaryLight : Theme.border
            border.width: 1

            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: I18n.currentLanguage === "fr" ? "EN" : "FR"
                color: Theme.textPrimary
                font.pixelSize: 12
                font.bold: true
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
                    I18n.setLanguage(I18n.currentLanguage === "fr" ? "en" : "fr");
                }
            }
        }

        // License Button (icon only; Green: Activated, Orange: Trial, Red: Not Activated)
        Rectangle {
            id: licenseBtn
            width: 36
            height: 36
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

            FaIcon {
                anchors.centerIn: parent
                icon: {
                    if (Bridge.isLicensed && !Bridge.isTrial) return Icons.checkCircle;
                    if (Bridge.isTrial) return Icons.clock;
                    return Icons.key;
                }
                size: 14
                iconColor: licenseBtn.statusColor
            }

            ToolTip.visible: licMouse.containsMouse
            ToolTip.text: {
                if (Bridge.isLicensed && !Bridge.isTrial) return I18n.t("status_licensed");
                if (Bridge.isTrial) return I18n.t("status_trial") + " (" + Bridge.trialDaysRemaining + "d)";
                return I18n.t("status_activation_required");
            }
            ToolTip.delay: 300

            MouseArea {
                id: licMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.openLicense()
            }
        }

        // Add Item Button (icon only)
        Rectangle {
            id: addBtn
            width: 36
            height: 36
            radius: Theme.radiusMd
            color: addMouse.containsMouse ? Theme.primaryHover : Theme.primary

            FaIcon {
                anchors.centerIn: parent
                icon: Icons.plus
                size: 14
                iconColor: "white"
            }

            MouseArea {
                id: addMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.addItemRequested()
            }

            ToolTip.visible: addMouse.containsMouse
            ToolTip.text: I18n.t("add_item_btn")
            ToolTip.delay: 300
        }
    }

    // =========================================================
    // Filter Popup (job / category / subcategory)
    // =========================================================
    Popup {
        id: filterPopup
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(440, parent.width - 40)
        height: implicitHeight + 23
        padding: 0
        modal: true
        dim: true
        focus: true
        closePolicy: Popup.CloseOnEscape

        background: Rectangle {
            color: Theme.surface
            border.color: Theme.border
            border.width: 1
            radius: 14
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 14

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                FaIcon { icon: Icons.filter; size: 12; iconColor: Theme.primaryLight }
                Text { text: I18n.t("filter_title"); color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
                Item { Layout.fillWidth: true }
                Rectangle {
                    width: 28; height: 28; radius: 14
                    color: closeFilterMouse.containsMouse ? Qt.rgba(255,255,255,0.12) : "transparent"
                    FaIcon { anchors.centerIn: parent; icon: Icons.times; size: 13; iconColor: closeFilterMouse.containsMouse ? Theme.textPrimary : Theme.textMuted }
                    MouseArea {
                        id: closeFilterMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: filterPopup.close()
                    }
                }
            }

            // Job filter (buttons, single row)
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8
                Text { text: I18n.t("filter_job_label"); color: Theme.textMuted; font.pixelSize: 11; font.bold: true }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Repeater {
                        model: [
                            { id: "all" },
                            { id: "architect" },
                            { id: "graphiste" },
                            { id: "video maker" }
                        ]

                        Rectangle {
                            id: jobBtn
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            property bool selected: root.jobFilter === modelData.id
                            radius: Theme.radiusMd
                            color: jobBtn.selected
                                ? Theme.primary
                                : (jobBtnMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : Theme.surfaceElevated)
                            border.color: jobBtn.selected ? Theme.primaryLight : Theme.border
                            border.width: 1

                            Behavior on color { ColorAnimation { duration: 120 } }

                            Text {
                                anchors.fill: parent
                                anchors.margins: 6
                                text: root.jobDisplay(modelData.id)
                                color: jobBtn.selected ? "white" : Theme.textPrimary
                                font.pixelSize: 11
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }

                            MouseArea {
                                id: jobBtnMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.jobFilter = modelData.id;
                                    root.emitFilter();
                                }
                            }
                        }
                    }
                }
            }

            // Category filter (dropdown)
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                Text { text: I18n.t("filter_category_label"); color: Theme.textMuted; font.pixelSize: 11; font.bold: true }
                Rectangle {
                    id: catSelectBox
                    Layout.fillWidth: true
                    height: 38
                    radius: Theme.radiusMd
                    color: Theme.surfaceElevated
                    border.color: catMenu.visible ? Theme.primary : Theme.border
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12; anchors.rightMargin: 10
                        spacing: 8
                        FaIcon { icon: Icons.layerGroup; size: 12; iconColor: Theme.primaryLight }
                        Text {
                            Layout.fillWidth: true
                            text: (root.categoryFilter === "all") ? I18n.t("all_categories") : root.categoryFilter
                            color: Theme.textPrimary
                            font.pixelSize: 12
                            elide: Text.ElideRight
                        }
                        FaIcon { icon: Icons.chevronDown; size: 10; iconColor: Theme.textMuted }
                    }

                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: catMenu.open() }

                    Menu {
                        id: catMenu
                        y: catSelectBox.height + 4
                        width: catSelectBox.width
                        background: Rectangle { color: Theme.surfaceElevated; border.color: Theme.border; radius: 8 }
                        delegate: MenuItem {
                            id: catItem
                            background: Rectangle {
                                color: catItem.highlighted ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : "transparent"
                                radius: 6
                            }
                            contentItem: Text {
                                text: catItem.text
                                color: catItem.highlighted ? Theme.primaryLight : Theme.textPrimary
                                font.pixelSize: 12
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 10
                            }
                        }
                        Repeater {
                            model: root.categoryOptions()
                            MenuItem {
                                text: modelData.label
                                font.bold: root.categoryFilter === modelData.name
                                onTriggered: {
                                    root.categoryFilter = modelData.name;
                                    root.subcategoryFilter = "all";
                                    root.emitFilter();
                                }
                            }
                        }
                    }
                }
            }

            // Footer actions
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 2
                spacing: 10
                Item { Layout.fillWidth: true }

                Rectangle {
                    Layout.minimumWidth: resetLbl.implicitWidth + 32
                    Layout.preferredWidth: resetLbl.implicitWidth + 32
                    height: 38
                    radius: Theme.radiusMd
                    color: resetMouse.containsMouse ? Theme.surfaceElevated : "transparent"
                    border.color: Theme.border
                    Text {
                        id: resetLbl
                        anchors.centerIn: parent
                        text: I18n.t("filter_clear_btn")
                        color: Theme.textPrimary
                        font.pixelSize: 12
                        font.bold: true
                    }
                    MouseArea {
                        id: resetMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.jobFilter = "all";
                            root.categoryFilter = "all";
                            root.subcategoryFilter = "all";
                            root.emitFilter();
                        }
                    }
                }

                Rectangle {
                    Layout.minimumWidth: doneLbl.implicitWidth + 32
                    Layout.preferredWidth: doneLbl.implicitWidth + 32
                    height: 38
                    radius: Theme.radiusMd
                    color: doneMouse.containsMouse ? Theme.primaryHover : Theme.primary
                    Text {
                        id: doneLbl
                        anchors.centerIn: parent
                        text: I18n.t("filter_apply_btn")
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                    }
                    MouseArea {
                        id: doneMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: filterPopup.close()
                    }
                }
            }
        }
    }
}
