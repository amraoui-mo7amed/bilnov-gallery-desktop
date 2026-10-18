import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "."

Rectangle {
    id: root
    parent: Overlay.overlay
    anchors.fill: parent
    color: "#E6030712"
    z: 99997
    visible: opacity > 0
    opacity: 0

    property string selectedFolder: ""
    property string selectedJob: "architect"
    property string errorMessage: ""
    property bool isSubmitting: false

    signal createNewJobRequested()

    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutQuad } }

    function open(folderPath) {
        selectedFolder = folderPath || ""
        categoryInput.text = ""
        categoryMenu.close()
        jobMenu.close()
        errorMessage = ""
        isSubmitting = false
        opacity = 1

        // Default to first job if selectedJob not in list
        var jobs = getJobOptions()
        var found = false
        for (var i = 0; i < jobs.length; i++) {
            if (jobs[i].id.toLowerCase() === selectedJob.toLowerCase()) {
                found = true
                break
            }
        }
        if (!found && jobs.length > 0) {
            selectedJob = jobs[0].id
        }
    }

    function close() {
        if (!isSubmitting) opacity = 0
    }

    function browseFolder() {
        var p = Bridge.pickFolder()
        if (p && p.length > 0) {
            selectedFolder = p
            errorMessage = ""
        }
    }

    property var jobOptionsList: {
        var base = [
            { id: "architect", name: "Architect", folder: "Architect" },
            { id: "graphiste", name: "Graphiste", folder: "Graphiste" },
            { id: "video maker", name: "Video Maker", folder: "Video Maker" }
        ]
        var extra = Bridge.jobOptions || []
        for (var i = 0; i < extra.length; i++) {
            var ej = extra[i]
            var exists = false
            for (var j = 0; j < base.length; j++) {
                if (base[j].id.toLowerCase() === ej.id.toLowerCase() || base[j].folder.toLowerCase() === ej.folder.toLowerCase()) {
                    exists = true
                    break
                }
            }
            if (!exists) {
                base.push({ id: ej.id, name: ej.name, folder: ej.folder })
            }
        }
        return base
    }

    property var categoryList: {
        var out = []
        var pre = Bridge.predefinedCategories || []
        for (var i = 0; i < pre.length; i++) {
            var p = String(pre[i])
            if (p && out.indexOf(p) < 0) out.push(p)
        }
        var cats = Bridge.categories || []
        for (var j = 0; j < cats.length; j++) {
            var c = cats[j]
            var n = (typeof c === "object" && c !== null) ? (c.name || c.title || "") : String(c)
            if (n && out.indexOf(n) < 0) out.push(n)
        }
        if (out.length === 0) {
            out = ["Architecture", "Furniture", "Decoration", "Lighting", "Materials", "Characters", "Vehicles", "Props"]
        }
        return out
    }

    function getJobOptions() {
        return jobOptionsList
    }

    function getJobDisplay(id) {
        if (!id) return "";
        if (id === "architect") return I18n.currentLanguage === "fr" ? "Architecte" : "Architect";
        if (id === "graphiste") return "Graphiste";
        if (id === "video maker") return "Video Maker";
        var jobs = jobOptionsList
        for (var i = 0; i < jobs.length; i++) {
            if (jobs[i].id.toLowerCase() === id.toLowerCase()) return jobs[i].name;
        }
        return id;
    }

    function categoryOptions() {
        return categoryList
    }

    function submit() {
        errorMessage = ""
        if (!selectedFolder || selectedFolder.trim() === "") {
            errorMessage = I18n.t("import_err_no_folder")
            return
        }

        isSubmitting = true
        var jobFolder = Bridge.getJobFolder(selectedJob) || selectedJob
        var cat = categoryInput.text.trim() || "General"
        Bridge.importFolder(selectedFolder, jobFolder, cat)
    }

    Connections {
        target: Bridge
        function onFolderImported(success, pathOrErr) {
            if (!root.visible) return
            root.isSubmitting = false
            if (success) {
                root.opacity = 0
            } else {
                root.errorMessage = I18n.tMsg(pathOrErr)
            }
        }
    }

    // Dismiss on backdrop click
    MouseArea {
        anchors.fill: parent
        onClicked: root.close()
    }

    // Modal Card
    Rectangle {
        id: modalCard
        width: Math.min(520, parent.width - 40)
        height: cardLayout.implicitHeight + 48
        anchors.centerIn: parent
        radius: Theme.radiusLg
        color: Theme.surface
        border.color: Theme.border
        border.width: 1

        MouseArea {
            anchors.fill: parent
            // prevent click-through
        }

        ColumnLayout {
            id: cardLayout
            anchors.fill: parent
            anchors.margins: 24
            spacing: 16

            // Header
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Rectangle {
                    width: 36
                    height: 36
                    radius: Theme.radiusMd
                    color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15)
                    border.color: Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.3)

                    FaIcon {
                        anchors.centerIn: parent
                        icon: Icons.folderOpen
                        size: 15
                        iconColor: Theme.primaryLight
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: I18n.t("import_folder_title")
                        color: Theme.textPrimary
                        font.pixelSize: 16
                        font.bold: true
                    }

                    Text {
                        text: I18n.t("import_folder_desc")
                        color: Theme.textMuted
                        font.pixelSize: 11
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                    }
                }

                // Close Button
                Rectangle {
                    width: 28
                    height: 28
                    radius: 14
                    color: closeMouse.containsMouse ? Qt.rgba(255, 255, 255, 0.1) : "transparent"

                    FaIcon {
                        anchors.centerIn: parent
                        icon: Icons.times
                        size: 12
                        iconColor: Theme.textMuted
                    }

                    MouseArea {
                        id: closeMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.close()
                    }
                }
            }

            // Separator
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.border
            }

            // Folder Picker Row
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                    text: I18n.t("import_selected_folder")
                    color: Theme.textPrimary
                    font.pixelSize: 12
                    font.bold: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 40
                    radius: Theme.radiusMd
                    color: Theme.surfaceElevated
                    border.color: root.selectedFolder ? Theme.primary : Theme.border
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 8
                        spacing: 8

                        FaIcon {
                            icon: Icons.folder
                            size: 14
                            iconColor: root.selectedFolder ? Theme.primaryLight : Theme.textMuted
                        }

                        Text {
                            Layout.fillWidth: true
                            text: root.selectedFolder || I18n.t("import_select_placeholder")
                            color: root.selectedFolder ? Theme.textPrimary : Theme.textMuted
                            font.pixelSize: 12
                            elide: Text.ElideMiddle
                        }

                        // Browse Button
                        Rectangle {
                            Layout.preferredWidth: 84
                            Layout.preferredHeight: 28
                            radius: 6
                            color: browseMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15)
                            border.color: Theme.primaryLight
                            border.width: 1

                            RowLayout {
                                anchors.centerIn: parent
                                spacing: 4

                                FaIcon {
                                    icon: Icons.folderOpen
                                    size: 10
                                    iconColor: Theme.primaryLight
                                }

                                Text {
                                    text: root.selectedFolder ? I18n.t("import_change_btn") : I18n.t("import_browse_btn")
                                    color: Theme.primaryLight
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }

                            MouseArea {
                                id: browseMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.browseFolder()
                            }
                        }
                    }
                }
            }

            // Job Row
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        text: I18n.t("add_job_label")
                        color: Theme.textPrimary
                        font.pixelSize: 12
                        font.bold: true
                    }

                    Item { Layout.fillWidth: true }

                    // Create New Job Button
                    Rectangle {
                        id: newJobBtn
                        implicitWidth: newJobRow.implicitWidth + 16
                        implicitHeight: 24
                        Layout.preferredWidth: implicitWidth
                        Layout.preferredHeight: implicitHeight
                        radius: 6
                        color: newJobMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.1)
                        border.color: newJobMouse.containsMouse ? Theme.primaryLight : Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.3)
                        border.width: 1

                        RowLayout {
                            id: newJobRow
                            anchors.centerIn: parent
                            spacing: 4
                            FaIcon { icon: Icons.plus; size: 10; iconColor: Theme.primaryLight }
                            Text {
                                text: I18n.t("new_job_btn")
                                color: Theme.primaryLight
                                font.pixelSize: 11
                                font.bold: true
                            }
                        }

                        MouseArea {
                            id: newJobMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.createNewJobRequested()
                        }
                    }
                }

                Rectangle {
                    id: jobSelectBox
                    Layout.fillWidth: true
                    height: 38
                    radius: Theme.radiusMd
                    color: Theme.surfaceElevated
                    border.color: jobMenu.visible ? Theme.primary : Theme.border
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 8

                        FaIcon {
                            icon: Icons.briefcase
                            size: 12
                            iconColor: Theme.primaryLight
                        }

                        Text {
                            text: root.getJobDisplay(root.selectedJob)
                            color: Theme.textPrimary
                            font.pixelSize: 13
                            font.bold: true
                            Layout.fillWidth: true
                            verticalAlignment: Text.AlignVCenter
                        }

                        FaIcon {
                            icon: Icons.chevronDown
                            size: 10
                            iconColor: Theme.textMuted
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: jobMenu.open()
                    }

                    Menu {
                        id: jobMenu
                        z: 100005
                        y: jobSelectBox.height + 4
                        width: jobSelectBox.width

                        contentItem: ListView {
                            implicitHeight: Math.min(220, contentHeight)
                            model: jobMenu.contentModel
                            clip: true
                            interactive: true
                            boundsBehavior: Flickable.StopAtBounds
                            ScrollBar.vertical: ScrollBar {
                                policy: ScrollBar.AsNeeded
                                width: 6
                                background: Rectangle { color: "transparent" }
                                contentItem: Rectangle {
                                    implicitWidth: 6
                                    radius: 3
                                    color: Qt.rgba(255, 255, 255, 0.25)
                                }
                            }
                        }

                        background: Rectangle {
                            color: Theme.surfaceElevated
                            border.color: Theme.border
                            radius: 8
                        }

                        delegate: MenuItem {
                            id: mi
                            background: Rectangle {
                                color: mi.highlighted ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : "transparent"
                                radius: 6
                            }
                            contentItem: Text {
                                text: mi.text
                                color: mi.highlighted ? Theme.primaryLight : Theme.textPrimary
                                font.pixelSize: 13
                                font.bold: mi.font.bold
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 10
                            }
                        }

                        Repeater {
                            model: root.jobOptionsList
                            MenuItem {
                                text: root.getJobDisplay(modelData.id)
                                font.bold: root.selectedJob.toLowerCase() === modelData.id.toLowerCase()
                                onTriggered: {
                                    root.selectedJob = modelData.id
                                }
                            }
                        }

                        MenuSeparator {
                            contentItem: Rectangle { implicitHeight: 1; color: Theme.border }
                        }

                        MenuItem {
                            text: "+ " + I18n.t("new_job_btn")
                            font.bold: true
                            onTriggered: root.createNewJobRequested()
                        }
                    }
                }
            }

            // Category Row
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: I18n.t("add_category_label")
                        color: Theme.textPrimary
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                    Text {
                        property bool isCustom: categoryInput.text.trim() !== "" && root.categoryOptions().indexOf(categoryInput.text.trim()) === -1
                        text: isCustom
                            ? "+ " + I18n.tMsg(I18n.t("create_new_category"), categoryInput.text.trim())
                            : I18n.t("add_category_hint")
                        color: isCustom ? Theme.success : Theme.textMuted
                        font.pixelSize: 11
                        font.bold: isCustom
                        elide: Text.ElideRight
                        Layout.maximumWidth: 280
                    }
                }

                Rectangle {
                    id: categoryBox
                    Layout.fillWidth: true
                    height: 38
                    radius: Theme.radiusMd
                    color: Theme.surfaceElevated
                    border.color: categoryInput.activeFocus || categoryMenu.visible ? Theme.primary : Theme.border
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 8
                        spacing: 8

                        TextInput {
                            id: categoryInput
                            Layout.fillWidth: true
                            verticalAlignment: TextInput.AlignVCenter
                            color: Theme.textPrimary
                            font.pixelSize: 13
                            selectByMouse: true
                            clip: true

                            Text {
                                anchors.fill: parent
                                verticalAlignment: Text.AlignVCenter
                                text: I18n.t("add_category_placeholder")
                                color: Theme.textMuted
                                font.pixelSize: 13
                                visible: !categoryInput.text
                            }
                        }

                        // Clear text button
                        Rectangle {
                            width: 22
                            height: 22
                            radius: 11
                            color: clearCatMouse.containsMouse ? Qt.rgba(255, 255, 255, 0.1) : "transparent"
                            visible: categoryInput.text.length > 0

                            FaIcon {
                                anchors.centerIn: parent
                                icon: Icons.times
                                size: 10
                                iconColor: Theme.textMuted
                            }

                            MouseArea {
                                id: clearCatMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: categoryInput.text = ""
                            }
                        }

                        // Dropdown trigger button
                        Rectangle {
                            id: categoryDropdownBtn
                            width: 32
                            height: 30
                            radius: 6
                            color: catDropMouse.containsMouse || categoryMenu.visible ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Qt.rgba(255, 255, 255, 0.05)
                            border.color: catDropMouse.containsMouse || categoryMenu.visible ? Theme.primaryLight : Qt.rgba(255, 255, 255, 0.1)
                            border.width: 1

                            FaIcon {
                                anchors.centerIn: parent
                                icon: Icons.chevronDown
                                size: 11
                                iconColor: categoryMenu.visible ? Theme.primaryLight : Theme.textPrimary
                            }

                            MouseArea {
                                id: catDropMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (categoryMenu.visible) categoryMenu.close()
                                    else categoryMenu.open()
                                }
                            }
                        }
                    }

                    Menu {
                        id: categoryMenu
                        z: 100005
                        y: categoryBox.height + 4
                        width: categoryBox.width

                        contentItem: ListView {
                            implicitHeight: Math.min(220, contentHeight)
                            model: categoryMenu.contentModel
                            clip: true
                            interactive: true
                            boundsBehavior: Flickable.StopAtBounds
                            ScrollBar.vertical: ScrollBar {
                                policy: ScrollBar.AsNeeded
                                width: 6
                                background: Rectangle { color: "transparent" }
                                contentItem: Rectangle {
                                    implicitWidth: 6
                                    radius: 3
                                    color: Qt.rgba(255, 255, 255, 0.25)
                                }
                            }
                        }

                        background: Rectangle {
                            color: Theme.surfaceElevated
                            border.color: Theme.border
                            radius: 8
                        }

                        delegate: MenuItem {
                            id: catMi
                            background: Rectangle {
                                color: catMi.highlighted ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : "transparent"
                                radius: 6
                            }
                            contentItem: Text {
                                text: catMi.text
                                color: catMi.highlighted ? Theme.primaryLight : Theme.textPrimary
                                font.pixelSize: 13
                                font.bold: catMi.font.bold
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 10
                            }
                        }

                        MenuItem {
                            text: (root.categoryList.length > 0)
                                ? ("— " + I18n.t("choose_category") + " (" + root.categoryList.length + ") —")
                                : ("— " + I18n.t("no_categories_available") + " —")
                            enabled: false
                        }

                        Repeater {
                            model: root.categoryList
                            MenuItem {
                                text: modelData
                                font.bold: categoryInput.text.trim().toLowerCase() === String(modelData).toLowerCase()
                                onTriggered: {
                                    categoryInput.text = modelData
                                }
                            }
                        }
                    }
                }
            }

            // Error display
            Text {
                text: root.errorMessage
                color: Theme.error
                font.pixelSize: 11
                visible: root.errorMessage.length > 0
                Layout.fillWidth: true
                wrapMode: Text.Wrap
            }

            // Actions
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                spacing: 10

                Item { Layout.fillWidth: true }

                // Cancel Button
                Rectangle {
                    Layout.preferredWidth: 90
                    Layout.preferredHeight: 36
                    radius: Theme.radiusMd
                    color: cancelMouse.containsMouse ? Qt.rgba(255, 255, 255, 0.08) : Theme.surfaceElevated
                    border.color: Theme.border
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: I18n.t("cancel")
                        color: Theme.textPrimary
                        font.pixelSize: 12
                        font.bold: true
                    }

                    MouseArea {
                        id: cancelMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.close()
                    }
                }

                // Import Button
                Rectangle {
                    Layout.preferredWidth: 140
                    Layout.preferredHeight: 36
                    radius: Theme.radiusMd
                    color: submitMouse.containsMouse ? Theme.primaryHover : Theme.primary
                    opacity: (!root.selectedFolder || root.isSubmitting) ? 0.6 : 1.0

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6

                        FaIcon {
                            icon: Icons.upload
                            size: 11
                            iconColor: "white"
                        }

                        Text {
                            text: root.isSubmitting ? I18n.t("import_submitting") : I18n.t("import_btn")
                            color: "white"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }

                    MouseArea {
                        id: submitMouse
                        anchors.fill: parent
                        enabled: !root.isSubmitting && root.selectedFolder.length > 0
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.submit()
                    }
                }
            }
        }
    }
}
