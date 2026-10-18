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
    z: 99996
    visible: opacity > 0
    opacity: 0

    property var images: []      // absolute local paths, index 0 = thumbnail
    property var models: []      // absolute local paths
    property bool isSubmitting: false
    property string errorMessage: ""
    property string selectedJob: "architect"
    property var jobOptions: [
        { id: "architect", folder: "Architect" },
        { id: "graphiste", folder: "Graphiste" },
        { id: "video maker", folder: "Video Maker" }
    ]

    signal createNewJobRequested()

    function getCombinedJobs() {
        var list = [
            { id: "architect", folder: "Architect" },
            { id: "graphiste", folder: "Graphiste" },
            { id: "video maker", folder: "Video Maker" }
        ];
        var extra = Bridge.jobOptions || [];
        for (var i = 0; i < extra.length; i++) {
            var ej = extra[i];
            var exists = false;
            for (var j = 0; j < list.length; j++) {
                if (list[j].id.toLowerCase() === (ej.id || "").toLowerCase() || list[j].folder.toLowerCase() === (ej.folder || "").toLowerCase()) {
                    exists = true;
                    break;
                }
            }
            if (!exists && ej.id) {
                list.push({ id: ej.id, folder: ej.folder || ej.name, name: ej.name });
            }
        }
        return list;
    }

    function refreshJobs() {
        jobOptions = getCombinedJobs();
    }

    function getJobDisplay(id) {
        if (id === "architect") return I18n.currentLanguage === "fr" ? "Architecte" : "Architect";
        if (id === "graphiste") return "Graphiste";
        if (id === "video maker") return "Video Maker";
        var jobs = Bridge.jobOptions || [];
        for (var i = 0; i < jobs.length; i++) {
            if (jobs[i].id && String(jobs[i].id).toLowerCase() === String(id).toLowerCase()) {
                return jobs[i].name || id;
            }
        }
        return id;
    }

    function getJobFolder(id) {
        if (id === "architect") return "Architect";
        if (id === "graphiste") return "Graphiste";
        if (id === "video maker") return "Video Maker";
        var jobs = Bridge.jobOptions || [];
        for (var i = 0; i < jobs.length; i++) {
            if (jobs[i].id && String(jobs[i].id).toLowerCase() === String(id).toLowerCase()) {
                return jobs[i].folder || id;
            }
        }
        return id || "Architect";
    }

    // Prefilled categories from the storage folder taxonomy, merged with the
    // categories already present in the library.
    function categoryOptions() {
        var out = [];
        var pre = Bridge.predefinedCategories || [];
        for (var i = 0; i < pre.length; i++) {
            var p = String(pre[i]);
            if (p && out.indexOf(p) < 0) out.push(p);
        }
        var cats = Bridge.categories || [];
        for (var j = 0; j < cats.length; j++) {
            var c = cats[j];
            var n = (typeof c === "object" && c !== null) ? (c.name || c.title || "") : String(c);
            if (n && out.indexOf(n) < 0) out.push(n);
        }
        if (out.length === 0) {
            out = ["Architecture", "Furniture", "Decoration", "Lighting", "Materials", "Characters", "Vehicles", "Props"];
        }
        return out;
    }

    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutQuad } }

    function open() {
        images = []
        models = []
        nameInput.text = ""
        refreshJobs()
        selectedJob = "architect"
        categoryInput.text = ""
        categoryMenu.close()
        jobMenu.close()
        errorMessage = ""
        isSubmitting = false
        opacity = 1
        nameInput.forceActiveFocus()
    }

    function close() {
        if (!isSubmitting) opacity = 0
    }

    function baseName(p) {
        var s = String(p)
        var i = Math.max(s.lastIndexOf("/"), s.lastIndexOf("\\"))
        return i >= 0 ? s.substring(i + 1) : s
    }

    function stem(p) {
        var b = baseName(p)
        var d = b.lastIndexOf(".")
        return d > 0 ? b.substring(0, d) : b
    }

    function addImages() {
        var picked = Bridge.pickImages()
        if (!picked || picked.length === 0) return
        var arr = images.slice()
        for (var i = 0; i < picked.length; i++) {
            if (arr.indexOf(picked[i]) < 0) arr.push(picked[i])
        }
        images = arr
    }

    function addModels() {
        var picked = Bridge.pickModelFiles()
        if (!picked || picked.length === 0) return
        var arr = models.slice()
        for (var i = 0; i < picked.length; i++) {
            if (arr.indexOf(picked[i]) < 0) arr.push(picked[i])
        }
        models = arr
        // Convenience: prefill the article name from the first SketchUp file
        if (nameInput.text.trim() === "" && models.length > 0)
            nameInput.text = stem(models[0]).replace(/[_-]+/g, " ")
    }

    function removeImage(idx) {
        var arr = images.slice(); arr.splice(idx, 1); images = arr
    }

    function makeThumbnail(idx) {
        if (idx <= 0) return
        var arr = images.slice()
        var it = arr.splice(idx, 1)[0]
        arr.unshift(it)
        images = arr
    }

    function removeModel(idx) {
        var arr = models.slice(); arr.splice(idx, 1); models = arr
    }

    function submit() {
        errorMessage = ""
        if (nameInput.text.trim() === "") { errorMessage = I18n.t("add_err_name"); return }
        if (images.length === 0) { errorMessage = I18n.t("add_err_images"); return }
        if (models.length === 0) { errorMessage = I18n.t("add_err_models"); return }
        isSubmitting = true
        var jobFolder = getJobFolder(selectedJob)
        Bridge.addLibraryItem(nameInput.text.trim(), images, models, jobFolder, categoryInput.text.trim())
    }

    Connections {
        target: Bridge
        function onJobsChanged() {
            root.refreshJobs()
        }
        function onItemAdded(success, msg) {
            if (!root.visible) return
            root.isSubmitting = false
            if (success) root.opacity = 0
            else root.errorMessage = I18n.tMsg(msg)
        }
    }

    Keys.onEscapePressed: close()

    // Backdrop
    MouseArea {
        anchors.fill: parent
        onClicked: root.close()
    }

    Rectangle {
        id: box
        width: Math.min(620, parent.width - 40)
        height: Math.min(contentCol.implicitHeight + 48, parent.height - 40)
        anchors.centerIn: parent
        radius: 14
        color: Theme.surface
        border.color: Theme.border
        border.width: 1
        // Exit / Close button pinned to top-right
        Rectangle {
            id: closeBtn
            width: 32
            height: 32
            radius: 16
            color: closeMouse.containsMouse ? Qt.rgba(255, 255, 255, 0.12) : "transparent"
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 16
            anchors.rightMargin: 16
            z: 20

            Behavior on color { ColorAnimation { duration: 120 } }

            FaIcon {
                anchors.centerIn: parent
                icon: Icons.times
                size: 14
                iconColor: closeMouse.containsMouse ? Theme.textPrimary : Theme.textMuted
            }

            MouseArea {
                id: closeMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.close()
            }
        }

        Flickable {
            id: flickable
            anchors.fill: parent
            anchors.margins: 24
            contentWidth: width
            contentHeight: contentCol.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            ColumnLayout {
                id: contentCol
                width: flickable.width
                spacing: 16

                // Header
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Rectangle {
                        width: 36; height: 36; radius: 10
                        color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15)
                        FaIcon { anchors.centerIn: parent; icon: Icons.plus; size: 14; iconColor: Theme.primaryLight }
                    }
                    ColumnLayout {
                        spacing: 2
                        Layout.fillWidth: true
                        Text { text: I18n.t("add_item_title"); color: Theme.textPrimary; font.pixelSize: 16; font.bold: true }
                        Text { text: I18n.t("add_item_subtitle"); color: Theme.textMuted; font.pixelSize: 11 }
                    }
                    Item { width: 32; height: 1 }
                }

                // Article name
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text { text: I18n.t("add_name_label") + " *"; color: Theme.textPrimary; font.pixelSize: 12; font.bold: true }
                    Rectangle {
                        Layout.fillWidth: true
                        height: 38
                        radius: Theme.radiusMd
                        color: Theme.surfaceElevated
                        border.color: nameInput.activeFocus ? Theme.primary : Theme.border
                        TextInput {
                            id: nameInput
                            anchors.fill: parent
                            anchors.leftMargin: 12; anchors.rightMargin: 12
                            verticalAlignment: TextInput.AlignVCenter
                            color: Theme.textPrimary
                            font.pixelSize: 13
                            selectByMouse: true
                            clip: true
                            Text {
                                anchors.fill: parent
                                verticalAlignment: Text.AlignVCenter
                                text: I18n.t("add_name_placeholder")
                                color: Theme.textMuted
                                font.pixelSize: 13
                                visible: !nameInput.text
                            }
                        }
                    }
                }

                // Job (replacing Category)
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
                        Rectangle {
                            id: newJobBtn
                            implicitWidth: newJobBtnRow.implicitWidth + 16
                            implicitHeight: 24
                            Layout.preferredWidth: implicitWidth
                            Layout.preferredHeight: implicitHeight
                            radius: 6
                            color: newJobBtnMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.1)
                            border.color: newJobBtnMouse.containsMouse ? Theme.primaryLight : Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.3)
                            border.width: 1

                            RowLayout {
                                id: newJobBtnRow
                                anchors.centerIn: parent
                                spacing: 4
                                FaIcon { icon: Icons.plus; size: 10; iconColor: Theme.primaryLight }
                                Text { text: I18n.t("new_job_btn"); color: Theme.primaryLight; font.pixelSize: 11; font.bold: true }
                            }
                            MouseArea {
                                id: newJobBtnMouse
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
                            layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

                            FaIcon {
                                icon: {
                                    if (root.selectedJob === "architect") return Icons.building;
                                    if (root.selectedJob === "graphiste") return Icons.image;
                                    return Icons.camera;
                                }
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
                            clip: true

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
                                model: root.jobOptions
                                MenuItem {
                                    text: root.getJobDisplay(modelData.id)
                                    font.bold: root.selectedJob === modelData.id
                                    onTriggered: {
                                        root.selectedJob = modelData.id;
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

                // Category (prefilled from the storage folder, or type your own)
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

                    // Input Box with clear & dropdown toggle
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

                            // Clear text button (if text present)
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

                            // Dropdown trigger button to choose a prefilled category
                            Rectangle {
                                id: categoryDropdownBtn
                                width: 28
                                height: 28
                                radius: 6
                                color: catBtnMouse.containsMouse || categoryMenu.visible ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.18) : "transparent"

                                FaIcon {
                                    anchors.centerIn: parent
                                    icon: Icons.chevronDown
                                    size: 11
                                    iconColor: categoryMenu.visible ? Theme.primaryLight : Theme.textMuted
                                }

                                MouseArea {
                                    id: catBtnMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (categoryMenu.visible) categoryMenu.close();
                                        else categoryMenu.open();
                                    }
                                }
                            }
                        }

                        // Dropdown menu showing prefilled categories from the storage folder
                        Menu {
                            id: categoryMenu
                            z: 100005
                            y: categoryBox.height + 4
                            width: categoryBox.width
                            clip: true
                            background: Rectangle {
                                color: Theme.surfaceElevated
                                border.color: Theme.border
                                radius: 8
                            }
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

                            MenuItem {
                                text: (root.categoryOptions().length > 0)
                                    ? ("— " + I18n.t("choose_category") + " (" + root.categoryOptions().length + ") —")
                                    : ("— " + I18n.t("no_categories_available") + " —")
                                enabled: false
                            }

                            Repeater {
                                model: root.categoryOptions()
                                MenuItem {
                                    text: modelData
                                    font.bold: categoryInput.text === modelData
                                    onTriggered: {
                                        categoryInput.text = modelData;
                                    }
                                }
                            }
                        }
                    }

                    // Quick-pick chips from the prefilled categories
                    Flow {
                        Layout.fillWidth: true
                        spacing: 6
                        visible: root.categoryOptions().length > 0

                        Repeater {
                            model: root.categoryOptions()
                            Rectangle {
                                property string catName: String(modelData)
                                height: 24
                                width: chipCatText.implicitWidth + 18
                                radius: 12
                                color: categoryInput.text === catName ? Theme.primary : Theme.surfaceElevated
                                border.color: categoryInput.text === catName ? Theme.primaryLight : Theme.border

                                Text {
                                    id: chipCatText
                                    anchors.centerIn: parent
                                    text: parent.catName
                                    color: categoryInput.text === parent.catName ? "white" : Theme.textMuted
                                    font.pixelSize: 10
                                    font.bold: categoryInput.text === parent.catName
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        categoryInput.text = parent.catName;
                                    }
                                }
                            }
                        }
                    }
                }

                // Images
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: I18n.t("add_images_label") + " * (" + root.images.length + ")"; color: Theme.textPrimary; font.pixelSize: 12; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Text { text: I18n.t("add_images_hint"); color: Theme.textMuted; font.pixelSize: 10 }
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 10

                        Repeater {
                            model: root.images
                            Rectangle {
                                width: 108; height: 84
                                radius: 8
                                color: Theme.surfaceElevated
                                border.color: index === 0 ? Theme.primary : Theme.border
                                border.width: index === 0 ? 2 : 1
                                clip: true

                                Image {
                                    anchors.fill: parent
                                    anchors.margins: 2
                                    source: Bridge.toFileUrl(modelData)
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                    sourceSize.width: 220
                                }

                                // Thumbnail badge / make-thumbnail star
                                Rectangle {
                                    anchors.left: parent.left; anchors.top: parent.top; anchors.margins: 4
                                    height: 18
                                    width: index === 0 ? thumbLbl.implicitWidth + 24 : 20
                                    radius: 9
                                    color: index === 0 ? Theme.primary : "#CC0F172A"
                                    RowLayout {
                                        anchors.centerIn: parent
                                        spacing: 4
                                        FaIcon { icon: Icons.star; size: 8; iconColor: index === 0 ? "white" : "#94A3B8" }
                                        Text { id: thumbLbl; visible: index === 0; text: I18n.t("thumbnail"); color: "white"; font.pixelSize: 9; font.bold: true }
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: index === 0 ? Qt.ArrowCursor : Qt.PointingHandCursor
                                        onClicked: root.makeThumbnail(index)
                                    }
                                }

                                // Remove
                                Rectangle {
                                    anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 4
                                    width: 18; height: 18; radius: 9
                                    color: "#CC0F172A"
                                    FaIcon { anchors.centerIn: parent; icon: Icons.times; size: 8; iconColor: "white" }
                                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.removeImage(index) }
                                }
                            }
                        }

                        // Add images tile
                        Rectangle {
                            width: 108; height: 84
                            radius: 8
                            color: addImgMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.12) : "transparent"
                            border.color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.5)
                            border.width: 1
                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: 6
                                FaIcon { Layout.alignment: Qt.AlignHCenter; icon: Icons.images; size: 16; iconColor: Theme.primaryLight }
                                Text { Layout.alignment: Qt.AlignHCenter; text: I18n.t("add_images_btn"); color: Theme.primaryLight; font.pixelSize: 10; font.bold: true }
                            }
                            MouseArea { id: addImgMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.addImages() }
                        }
                    }
                }

                // SketchUp files
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text { text: I18n.t("add_models_label") + " * (" + root.models.length + ")"; color: Theme.textPrimary; font.pixelSize: 12; font.bold: true }

                    Repeater {
                        model: root.models
                        Rectangle {
                            Layout.fillWidth: true
                            height: 36
                            radius: Theme.radiusSm
                            color: Theme.surfaceElevated
                            border.color: Theme.border
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12; anchors.rightMargin: 10
                                spacing: 10
                                FaIcon { icon: Icons.cube; size: 12; iconColor: Theme.primaryLight }
                                Text {
                                    Layout.fillWidth: true
                                    text: root.baseName(modelData)
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    elide: Text.ElideMiddle
                                }
                                FaIcon {
                                    icon: Icons.trash; size: 11; iconColor: Theme.textMuted
                                    MouseArea { anchors.fill: parent; anchors.margins: -6; cursorShape: Qt.PointingHandCursor; onClicked: root.removeModel(index) }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 38
                        radius: Theme.radiusSm
                        color: addModelMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.12) : "transparent"
                        border.color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.5)
                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            FaIcon { icon: Icons.upload; size: 12; iconColor: Theme.primaryLight }
                            Text { text: I18n.t("add_models_btn"); color: Theme.primaryLight; font.pixelSize: 12; font.bold: true }
                        }
                        MouseArea { id: addModelMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.addModels() }
                    }
                }

                // Error
                Text {
                    Layout.fillWidth: true
                    visible: root.errorMessage !== ""
                    text: root.errorMessage
                    color: Theme.error
                    font.pixelSize: 12
                    wrapMode: Text.Wrap
                }

                // Actions
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    spacing: 10
                    Item { Layout.fillWidth: true }

                    Rectangle {
                        Layout.minimumWidth: cancelLbl.implicitWidth + 32
                        Layout.preferredWidth: cancelLbl.implicitWidth + 32
                        Layout.maximumWidth: 210
                        height: 38
                        radius: Theme.radiusMd
                        color: cancelMouse.containsMouse ? Theme.surfaceElevated : "transparent"
                        border.color: Theme.border
                        Text { id: cancelLbl; anchors.centerIn: parent; text: I18n.t("cancel"); color: Theme.textPrimary; font.pixelSize: 12; font.bold: true }
                        MouseArea { id: cancelMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.close() }
                    }

                    Rectangle {
                        Layout.minimumWidth: saveRow.implicitWidth + 32
                        Layout.preferredWidth: saveRow.implicitWidth + 32
                        Layout.maximumWidth: 210
                        height: 38
                        radius: Theme.radiusMd
                        opacity: root.isSubmitting ? 0.6 : 1
                        color: saveMouse.containsMouse ? Theme.primaryHover : Theme.primary
                        RowLayout {
                            id: saveRow
                            anchors.centerIn: parent
                            spacing: 8
                            FaIcon { icon: root.isSubmitting ? Icons.sync : Icons.check; size: 12; iconColor: "white" }
                            Text { text: root.isSubmitting ? I18n.t("add_saving") : I18n.t("add_save_btn"); color: "white"; font.pixelSize: 12; font.bold: true }
                        }
                        MouseArea {
                            id: saveMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            enabled: !root.isSubmitting
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.submit()
                        }
                    }
                }
            }
        }
    }
}
