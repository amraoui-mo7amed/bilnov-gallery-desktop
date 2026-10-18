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

    // Active filter state (job = top level folder, category = second level folder)
    property string jobFilter: "all"
    property string categoryFilter: "all"

    signal searchRequested(string query)
    signal openLicense()
    signal addItemRequested()
    signal importFolderRequested()
    signal createNewJobRequested()
    signal filterChanged(string job, string category, string subcategory)

    function jobDisplay(id) {
        if (id === "all") return I18n.t("all_jobs");
        if (id === "architect") return I18n.t("job_architect");
        if (id === "graphiste") return I18n.t("job_graphiste");
        if (id === "video maker") return I18n.t("job_video_maker");
        var jobs = Bridge.jobOptions || [];
        for (var i = 0; i < jobs.length; i++) {
            if (jobs[i].id && String(jobs[i].id).toLowerCase() === String(id).toLowerCase()) {
                return jobs[i].name || id;
            }
        }
        return id;
    }

    function jobFolder(id) {
        if (id === "architect") return "Architect";
        if (id === "graphiste") return "Graphiste";
        if (id === "video maker") return "Video Maker";
        var jobs = Bridge.jobOptions || [];
        for (var i = 0; i < jobs.length; i++) {
            if (jobs[i].id && String(jobs[i].id).toLowerCase() === String(id).toLowerCase()) {
                return jobs[i].folder || id;
            }
        }
        return id;
    }

    function getFilterJobOptions() {
        var base = [
            { id: "all" },
            { id: "architect" },
            { id: "graphiste" },
            { id: "video maker" }
        ];
        var jobs = Bridge.jobOptions || [];
        for (var i = 0; i < jobs.length; i++) {
            var j = jobs[i];
            var exists = false;
            for (var k = 0; k < base.length; k++) {
                if (base[k].id.toLowerCase() === (j.id || "").toLowerCase()) {
                    exists = true;
                    break;
                }
            }
            if (!exists && j.id) {
                base.push({ id: j.id });
            }
        }
        return base;
    }

    function categoryOptions() {
        var arr = [{ name: "all", label: I18n.t("all_categories") }];
        // Depend on libraryItems so options refresh when storage changes.
        void Bridge.libraryItems.length;
        var map = Bridge.subcategoryMap || {};
        var names = [];
        if (root.jobFilter && root.jobFilter !== "all") {
            names = (map[root.jobFolder(root.jobFilter)] || []).slice();
        } else {
            for (var k in map) {
                var lst = map[k] || [];
                for (var j = 0; j < lst.length; j++) {
                    if (names.indexOf(lst[j]) === -1) names.push(lst[j]);
                }
            }
        }
        names.sort(function(a, b) { return a.toLowerCase().localeCompare(b.toLowerCase()); });
        for (var i = 0; i < names.length; i++) arr.push({ name: names[i], label: names[i] });
        return arr;
    }

    function emitFilter() {
        root.filterChanged(root.jobFilter, "all", root.categoryFilter);
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

            readonly property bool hasActiveFilter: root.jobFilter !== "all" || root.categoryFilter !== "all"

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

        // Import Folder Button (icon only)
        Rectangle {
            id: importFolderBtn
            width: 36
            height: 36
            radius: Theme.radiusMd
            color: importFolderMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : Theme.surfaceElevated
            border.color: importFolderMouse.containsMouse ? Theme.primaryLight : Theme.border
            border.width: 1

            Behavior on color { ColorAnimation { duration: 150 } }

            FaIcon {
                anchors.centerIn: parent
                icon: Icons.folderOpen
                size: 14
                iconColor: Theme.textPrimary
            }

            MouseArea {
                id: importFolderMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.importFolderRequested()
            }

            ToolTip.visible: importFolderMouse.containsMouse
            ToolTip.text: I18n.t("import_folder_btn")
            ToolTip.delay: 300
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
        width: Math.min(500, parent.width - 40)
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

            // Job filter
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: I18n.t("filter_job_label"); color: Theme.textMuted; font.pixelSize: 11; font.bold: true }
                    Item { Layout.fillWidth: true }

                    Rectangle {
                        id: newJobFilterBtn
                        implicitWidth: newJobFilterRow.implicitWidth + 16
                        implicitHeight: 24
                        Layout.preferredWidth: implicitWidth
                        Layout.preferredHeight: implicitHeight
                        radius: 6
                        color: newJobFilterMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.1)
                        border.color: newJobFilterMouse.containsMouse ? Theme.primaryLight : Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.3)
                        border.width: 1

                        RowLayout {
                            id: newJobFilterRow
                            anchors.centerIn: parent
                            spacing: 5
                            FaIcon { icon: Icons.plus; size: 9; iconColor: Theme.primaryLight }
                            Text {
                                text: I18n.t("new_job_btn")
                                color: Theme.primaryLight
                                font.pixelSize: 11
                                font.bold: true
                            }
                        }

                        MouseArea {
                            id: newJobFilterMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                filterPopup.close();
                                root.createNewJobRequested();
                            }
                        }
                    }
                }

                // 4 or fewer jobs: standard RowLayout (expanded to full width)
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    visible: root.getFilterJobOptions().length <= 4

                    Repeater {
                        model: root.getFilterJobOptions().length <= 4 ? root.getFilterJobOptions() : []

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
                                anchors.margins: 4
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
                                    root.categoryFilter = "all";
                                    root.emitFilter();
                                }
                            }
                        }
                    }
                }

                // More than 4 jobs: wrap in Flow
                Flow {
                    Layout.fillWidth: true
                    spacing: 8
                    visible: root.getFilterJobOptions().length > 4

                    Repeater {
                        model: root.getFilterJobOptions().length > 4 ? root.getFilterJobOptions() : []

                        Rectangle {
                            id: flowJobBtn
                            implicitWidth: Math.max(90, flowJobText.implicitWidth + 24)
                            implicitHeight: 34
                            property bool selected: root.jobFilter === modelData.id
                            radius: Theme.radiusMd
                            color: flowJobBtn.selected
                                ? Theme.primary
                                : (flowJobMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : Theme.surfaceElevated)
                            border.color: flowJobBtn.selected ? Theme.primaryLight : Theme.border
                            border.width: 1

                            Behavior on color { ColorAnimation { duration: 120 } }

                            Text {
                                id: flowJobText
                                anchors.centerIn: parent
                                text: root.jobDisplay(modelData.id)
                                color: flowJobBtn.selected ? "white" : Theme.textPrimary
                                font.pixelSize: 11
                                font.bold: true
                            }

                            MouseArea {
                                id: flowJobMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.jobFilter = modelData.id;
                                    root.categoryFilter = "all";
                                    root.emitFilter();
                                }
                            }
                        }
                    }
                }
            }

            // Category filter (dropdown, sourced from the storage taxonomy)
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                Text { text: I18n.t("filter_category_label"); color: Theme.textMuted; font.pixelSize: 11; font.bold: true }
                Rectangle {
                    id: categorySelectBox
                    Layout.fillWidth: true
                    height: 38
                    radius: Theme.radiusMd
                    color: Theme.surfaceElevated
                    border.color: categoryPopup.visible ? Theme.primary : Theme.border
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

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            categoryPopup.open();
                        }
                    }

                    Popup {
                        id: categoryPopup
                        parent: categorySelectBox
                        x: 0
                        y: categorySelectBox.height + 4
                        width: categorySelectBox.width
                        height: Math.min(categoryList.contentHeight + 8, 260)
                        padding: 4
                        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

                        background: Rectangle {
                            color: Theme.surfaceElevated
                            border.color: Theme.border
                            border.width: 1
                            radius: 8
                        }

                        ListView {
                            id: categoryList
                            anchors.fill: parent
                            clip: true
                            boundsBehavior: Flickable.StopAtBounds
                            model: root.categoryOptions()

                            ScrollBar.vertical: ScrollBar {
                                id: categoryScroll
                                active: true
                                policy: categoryList.contentHeight > categoryList.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                            }

                            ScrollBar.horizontal: ScrollBar {
                                policy: categoryList.contentWidth > categoryList.width ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                            }

                            delegate: Rectangle {
                                id: categoryRow
                                width: categoryList.width
                                height: 32
                                radius: 6
                                color: categoryRowMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : "transparent"

                                Text {
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 10
                                    text: modelData.label
                                    color: root.categoryFilter === modelData.name ? Theme.primaryLight : Theme.textPrimary
                                    font.pixelSize: 12
                                    font.bold: root.categoryFilter === modelData.name
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight
                                }

                                MouseArea {
                                    id: categoryRowMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        root.categoryFilter = modelData.name;
                                        categoryPopup.close();
                                        root.emitFilter();
                                    }
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
