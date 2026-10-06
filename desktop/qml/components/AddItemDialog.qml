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

    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutQuad } }

    function open() {
        images = []
        models = []
        nameInput.text = ""
        categoryInput.text = ""
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
        Bridge.addLibraryItem(nameInput.text.trim(), images, models, categoryInput.text.trim())
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
        clip: true

        MouseArea { anchors.fill: parent }   // swallow clicks

        Flickable {
            anchors.fill: parent
            anchors.margins: 24
            contentHeight: contentCol.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            ColumnLayout {
                id: contentCol
                width: parent.width
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
                    FaIcon {
                        icon: Icons.times; size: 14; iconColor: Theme.textMuted
                        MouseArea { anchors.fill: parent; anchors.margins: -6; cursorShape: Qt.PointingHandCursor; onClicked: root.close() }
                    }
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

                // Category (optional)
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text { text: I18n.t("add_category_label"); color: Theme.textPrimary; font.pixelSize: 12; font.bold: true }
                    Rectangle {
                        Layout.fillWidth: true
                        height: 38
                        radius: Theme.radiusMd
                        color: Theme.surfaceElevated
                        border.color: categoryInput.activeFocus ? Theme.primary : Theme.border
                        TextInput {
                            id: categoryInput
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
                                text: I18n.t("add_category_placeholder")
                                color: Theme.textMuted
                                font.pixelSize: 13
                                visible: !categoryInput.text
                            }
                        }
                    }
                    // Quick pick from existing categories
                    Flow {
                        Layout.fillWidth: true
                        spacing: 6
                        visible: Bridge.categories && Bridge.categories.length > 0
                        Repeater {
                            model: Bridge.categories
                            Rectangle {
                                property string catName: modelData.name || modelData.title || ""
                                height: 24
                                width: chipText.implicitWidth + 18
                                radius: 12
                                color: categoryInput.text === catName ? Theme.primary : Theme.surfaceElevated
                                border.color: Theme.border
                                Text {
                                    id: chipText
                                    anchors.centerIn: parent
                                    text: parent.catName
                                    color: categoryInput.text === parent.catName ? "white" : Theme.textMuted
                                    font.pixelSize: 10
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: categoryInput.text = parent.catName
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
                        width: 110; height: 38
                        radius: Theme.radiusMd
                        color: cancelMouse.containsMouse ? Theme.surfaceElevated : "transparent"
                        border.color: Theme.border
                        Text { anchors.centerIn: parent; text: I18n.t("cancel"); color: Theme.textPrimary; font.pixelSize: 12; font.bold: true }
                        MouseArea { id: cancelMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.close() }
                    }

                    Rectangle {
                        width: 160; height: 38
                        radius: Theme.radiusMd
                        opacity: root.isSubmitting ? 0.6 : 1
                        color: saveMouse.containsMouse ? Theme.primaryHover : Theme.primary
                        RowLayout {
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
