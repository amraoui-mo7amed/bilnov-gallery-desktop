import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "."

Rectangle {
    id: root
    anchors.fill: parent
    color: "#E6030712"
    z: 99000
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

    function getJobDisplay(id) {
        if (id === "architect") return I18n.currentLanguage === "fr" ? "Architecte" : "Architect";
        if (id === "graphiste") return "Graphiste";
        if (id === "video maker") return "Video Maker";
        return id;
    }

    function getJobFolder(id) {
        if (id === "architect") return "Architect";
        if (id === "graphiste") return "Graphiste";
        if (id === "video maker") return "Video Maker";
        return id || "Architect";
    }

    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutQuad } }

    function open() {
        images = []
        models = []
        nameInput.text = ""
        selectedJob = "architect"
        subcategoryInput.text = ""
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
        Bridge.addLibraryItem(nameInput.text.trim(), images, models, jobFolder, subcategoryInput.text.trim())
    }

    Connections {
        target: Bridge
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

                    Text {
                        text: I18n.t("add_job_label")
                        color: Theme.textPrimary
                        font.pixelSize: 12
                        font.bold: true
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
                            y: jobSelectBox.height + 4
                            width: jobSelectBox.width

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
                        }
                    }
                }

                // Subcategory (choose from library or create another one)
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: I18n.t("add_subcategory_label")
                            color: Theme.textPrimary
                            font.pixelSize: 12
                            font.bold: true
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: subcategoryInput.text.trim() !== "" && (Bridge.librarySubcategories || []).indexOf(subcategoryInput.text.trim()) === -1
                                ? "+ " + I18n.tMsg(I18n.t("create_new_subcat"), subcategoryInput.text.trim())
                                : ""
                            color: Theme.success
                            font.pixelSize: 11
                            font.bold: true
                            visible: text !== ""
                        }
                    }

                    // Input Box with clear & dropdown toggle
                    Rectangle {
                        id: subcatBox
                        Layout.fillWidth: true
                        height: 38
                        radius: Theme.radiusMd
                        color: Theme.surfaceElevated
                        border.color: subcategoryInput.activeFocus || subcatMenu.visible ? Theme.primary : Theme.border
                        border.width: 1

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 8
                            spacing: 8

                            TextInput {
                                id: subcategoryInput
                                Layout.fillWidth: true
                                verticalAlignment: TextInput.AlignVCenter
                                color: Theme.textPrimary
                                font.pixelSize: 13
                                selectByMouse: true
                                clip: true

                                Text {
                                    anchors.fill: parent
                                    verticalAlignment: Text.AlignVCenter
                                    text: I18n.t("add_subcategory_placeholder")
                                    color: Theme.textMuted
                                    font.pixelSize: 13
                                    visible: !subcategoryInput.text
                                }
                            }

                            // Clear text button (if text present)
                            Rectangle {
                                width: 22
                                height: 22
                                radius: 11
                                color: clearSubMouse.containsMouse ? Qt.rgba(255, 255, 255, 0.1) : "transparent"
                                visible: subcategoryInput.text.length > 0

                                FaIcon {
                                    anchors.centerIn: parent
                                    icon: Icons.times
                                    size: 10
                                    iconColor: Theme.textMuted
                                }

                                MouseArea {
                                    id: clearSubMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: subcategoryInput.text = ""
                                }
                            }

                            // Dropdown trigger button to choose from library
                            Rectangle {
                                id: subcatDropdownBtn
                                width: 28
                                height: 28
                                radius: 6
                                color: subcatBtnMouse.containsMouse || subcatMenu.visible ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.18) : "transparent"

                                FaIcon {
                                    anchors.centerIn: parent
                                    icon: Icons.chevronDown
                                    size: 11
                                    iconColor: subcatMenu.visible ? Theme.primaryLight : Theme.textMuted
                                }

                                MouseArea {
                                    id: subcatBtnMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (subcatMenu.visible) subcatMenu.close();
                                        else subcatMenu.open();
                                    }
                                }
                            }
                        }

                        // Dropdown menu showing existing subcategories from library
                        Menu {
                            id: subcatMenu
                            y: subcatBox.height + 4
                            width: subcatBox.width
                            background: Rectangle {
                                color: Theme.surfaceElevated
                                border.color: Theme.border
                                radius: 8
                            }
                            delegate: MenuItem {
                                id: subItem
                                background: Rectangle {
                                    color: subItem.highlighted ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : "transparent"
                                    radius: 6
                                }
                                contentItem: Text {
                                    text: subItem.text
                                    color: subItem.highlighted ? Theme.primaryLight : Theme.textPrimary
                                    font.pixelSize: 12
                                    verticalAlignment: Text.AlignVCenter
                                    leftPadding: 10
                                }
                            }

                            MenuItem {
                                text: (Bridge.librarySubcategories && Bridge.librarySubcategories.length > 0)
                                    ? ("— " + I18n.t("choose_from_library") + " (" + Bridge.librarySubcategories.length + ") —")
                                    : ("— " + I18n.t("no_library_subcats") + " —")
                                enabled: false
                            }

                            Repeater {
                                model: Bridge.librarySubcategories || []
                                MenuItem {
                                    text: modelData
                                    font.bold: subcategoryInput.text === modelData
                                    onTriggered: {
                                        subcategoryInput.text = modelData;
                                    }
                                }
                            }
                        }
                    }

                    // Quick-pick Chips from Library
                    Flow {
                        Layout.fillWidth: true
                        spacing: 6
                        visible: Bridge.librarySubcategories && Bridge.librarySubcategories.length > 0

                        Repeater {
                            model: Bridge.librarySubcategories || []
                            Rectangle {
                                property string subName: String(modelData)
                                height: 24
                                width: chipSubText.implicitWidth + 18
                                radius: 12
                                color: subcategoryInput.text === subName ? Theme.primary : Theme.surfaceElevated
                                border.color: subcategoryInput.text === subName ? Theme.primaryLight : Theme.border

                                Text {
                                    id: chipSubText
                                    anchors.centerIn: parent
                                    text: parent.subName
                                    color: subcategoryInput.text === parent.subName ? "white" : Theme.textMuted
                                    font.pixelSize: 10
                                    font.bold: subcategoryInput.text === parent.subName
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        subcategoryInput.text = parent.subName;
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
