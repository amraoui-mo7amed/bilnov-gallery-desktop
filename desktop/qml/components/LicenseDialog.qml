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
    z: 99995
    visible: opacity > 0
    opacity: 0

    property bool isSubmitting: false
    property string errorMessage: ""
    property string successMessage: ""

    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutQuad } }

    function open() {
        errorMessage = ""
        successMessage = ""
        isSubmitting = false
        keyInput.text = Bridge.licenseKey || ""
        opacity = 1
        keyInput.forceActiveFocus()
    }

    function close() {
        if (!isSubmitting) opacity = 0
    }

    function submitKey() {
        errorMessage = ""
        successMessage = ""
        var k = keyInput.text.trim()
        if (k.length < 10) {
            errorMessage = I18n.t("license_key_empty_err")
            return
        }
        isSubmitting = true
        Bridge.activateLicense(k)
    }

    Connections {
        target: Bridge
        function onActivationResult(success, msg) {
            if (!root.visible) return
            root.isSubmitting = false
            if (success) {
                root.errorMessage = ""
                root.successMessage = I18n.tMsg(msg)
            } else {
                root.errorMessage = I18n.tMsg(msg)
                root.successMessage = ""
            }
        }
    }

    Keys.onEscapePressed: close()

    // Backdrop click dismisses modal
    MouseArea {
        anchors.fill: parent
        onClicked: root.close()
    }

    // Modal Card
    Rectangle {
        id: box
        width: Math.min(540, parent.width - 32)
        height: Math.min(contentCol.implicitHeight + 48, parent.height - 40)
        anchors.centerIn: parent
        radius: 14
        color: Theme.surface
        border.color: Theme.border
        border.width: 1
        clip: true

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
                    spacing: 12
                    layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

                    Rectangle {
                        width: 36
                        height: 36
                        radius: 8
                        color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2)
                        border.color: Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.4)
                        FaIcon {
                            anchors.centerIn: parent
                            icon: Icons.key
                            size: 15
                            iconColor: Theme.primaryLight
                        }
                    }

                    ColumnLayout {
                        spacing: 2
                        Layout.fillWidth: true
                        Text {
                            text: I18n.t("license_modal_title")
                            color: Theme.textPrimary
                            font.pixelSize: 16
                            font.bold: true
                            horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                        }
                        Text {
                            text: I18n.t("license_modal_subtitle")
                            color: Theme.textMuted
                            font.pixelSize: 11
                            horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                        }
                    }

                    // Spacer so text does not overlap the top-right exit button
                    Item {
                        width: 32
                        height: 1
                    }
                }
                // -------------------------------------------------------------
                // 1. License Key Input Widget
                // -------------------------------------------------------------
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text {
                        text: I18n.t("license_key_label")
                        color: Theme.textPrimary
                        font.pixelSize: 12
                        font.bold: true
                        horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

                        Rectangle {
                            Layout.fillWidth: true
                            height: 40
                            radius: Theme.radiusMd
                            color: Theme.surfaceElevated
                            border.color: keyInput.activeFocus ? Theme.primary : Theme.border

                            TextInput {
                                id: keyInput
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                verticalAlignment: TextInput.AlignVCenter
                                color: Theme.textPrimary
                                font.pixelSize: 13
                                font.family: "Monospace"
                                selectByMouse: true
                                clip: true

                                Text {
                                    anchors.fill: parent
                                    verticalAlignment: Text.AlignVCenter
                                    text: I18n.t("license_key_placeholder")
                                    color: Theme.textMuted
                                    font.pixelSize: 12
                                    font.family: "Monospace"
                                    visible: !keyInput.text
                                }

                                Keys.onReturnPressed: root.submitKey()
                            }
                        }

                        // Activate Button
                        Rectangle {
                            Layout.minimumWidth: actBtnRow.implicitWidth + 32
                            Layout.preferredWidth: actBtnRow.implicitWidth + 32
                            height: 40
                            radius: Theme.radiusMd
                            color: actMouse.containsMouse ? Theme.primaryHover : Theme.primary
                            opacity: root.isSubmitting ? 0.6 : 1

                            RowLayout {
                                id: actBtnRow
                                anchors.centerIn: parent
                                spacing: 6
                                FaIcon {
                                    icon: root.isSubmitting ? Icons.sync : Icons.check
                                    size: 11
                                    iconColor: "white"
                                }
                                Text {
                                    text: root.isSubmitting ? I18n.t("license_activating") : I18n.t("license_activate_btn")
                                    color: "white"
                                    font.pixelSize: 12
                                    font.bold: true
                                }
                            }

                            MouseArea {
                                id: actMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                enabled: !root.isSubmitting
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.submitKey()
                            }
                        }
                    }

                    // Error text
                    Text {
                        visible: root.errorMessage.length > 0
                        text: root.errorMessage
                        color: Theme.error
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }

                    // Success text
                    Text {
                        visible: root.successMessage.length > 0
                        text: root.successMessage
                        color: Theme.success
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }

                // -------------------------------------------------------------
                // 3. Support & Contact Phone Numbers Card
                // -------------------------------------------------------------
                Rectangle {
                    Layout.fillWidth: true
                    radius: Theme.radiusMd
                    color: Theme.surfaceElevated
                    border.color: Theme.border
                    border.width: 1
                    implicitHeight: contactCol.implicitHeight + 24

                    ColumnLayout {
                        id: contactCol
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 10

                        Text {
                            text: I18n.t("contact_support_title")
                            color: Theme.textPrimary
                            font.pixelSize: 12
                            font.bold: true
                            horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                        }

                        Text {
                            text: I18n.t("contact_support_subtitle")
                            color: Theme.textMuted
                            font.pixelSize: 11
                            horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16
                            layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

                            Repeater {
                                model: [
                                    { raw: "+213775189229", display: "+213 775 18 92 29" },
                                    { raw: "+213673782115", display: "+213 673 78 21 15" }
                                ]

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 38
                                    radius: Theme.radiusSm
                                    color: Theme.card
                                    border.color: phoneBoxMouse.containsMouse ? Theme.primaryLight : Theme.border

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 10
                                        anchors.rightMargin: 8
                                        spacing: 8
                                        layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

                                        FaIcon {
                                            icon: Icons.phone
                                            size: 11
                                            iconColor: Theme.primaryLight
                                        }

                                        Text {
                                            text: modelData.display
                                            color: Theme.textPrimary
                                            font.pixelSize: 11
                                            font.family: "Monospace"
                                            font.bold: true
                                            Layout.fillWidth: true
                                        }

                                        Rectangle {
                                            width: 26
                                            height: 26
                                            radius: 6
                                            color: copyBtnMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Theme.surfaceElevated
                                            border.color: copyBtnMouse.containsMouse ? Theme.primary : Theme.border

                                            FaIcon {
                                                anchors.centerIn: parent
                                                icon: Icons.copy
                                                size: 11
                                                iconColor: copyBtnMouse.containsMouse ? Theme.primaryLight : Theme.textMuted
                                            }

                                            ToolTip.visible: copyBtnMouse.containsMouse
                                            ToolTip.text: I18n.t("copy_phone_toast")
                                            ToolTip.delay: 200

                                            MouseArea {
                                                id: copyBtnMouse
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: {
                                                    Bridge.copyToClipboard(modelData.raw)
                                                    Bridge.toast("info", I18n.t("copy_phone_toast"))
                                                }
                                            }
                                        }
                                    }

                                    MouseArea {
                                        id: phoneBoxMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            Bridge.copyToClipboard(modelData.raw)
                                            Bridge.toast("info", I18n.t("copy_phone_toast"))
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
