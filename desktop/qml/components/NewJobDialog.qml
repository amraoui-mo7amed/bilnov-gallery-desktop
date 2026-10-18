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
    z: 99998
    visible: opacity > 0
    opacity: 0

    property string targetCaller: "" // "addItem", "importFolder", "header"
    property string errorMessage: ""
    property bool isSubmitting: false

    signal jobCreated(string jobName, string targetCaller)

    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutQuad } }

    function openForTarget(caller) {
        targetCaller = caller || ""
        jobNameInput.text = ""
        errorMessage = ""
        isSubmitting = false
        opacity = 1
        jobNameInput.forceActiveFocus()
    }

    function close() {
        if (!isSubmitting) opacity = 0
    }

    function submit() {
        errorMessage = ""
        var name = jobNameInput.text.trim()
        if (name === "") {
            errorMessage = I18n.t("job_err_empty")
            return
        }

        // Check if job already exists locally in jobOptions
        var jobs = Bridge.jobOptions || []
        for (var i = 0; i < jobs.length; i++) {
            if (jobs[i].name && jobs[i].name.toLowerCase() === name.toLowerCase()) {
                errorMessage = I18n.t("job_err_exists")
                return
            }
        }

        isSubmitting = true
        var ok = Bridge.createJob(name)
        isSubmitting = false
        if (ok) {
            root.jobCreated(name, root.targetCaller)
            root.close()
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
        width: Math.min(420, parent.width - 40)
        height: cardLayout.implicitHeight + 48
        anchors.centerIn: parent
        radius: Theme.radiusLg
        color: Theme.surface
        border.color: Theme.border
        border.width: 1

        MouseArea {
            anchors.fill: parent
            // prevent click-through to backdrop
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
                        icon: Icons.briefcase
                        size: 15
                        iconColor: Theme.primaryLight
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: I18n.t("create_job_title")
                        color: Theme.textPrimary
                        font.pixelSize: 16
                        font.bold: true
                    }

                    Text {
                        text: I18n.t("create_job_desc")
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

            // Input Field
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                    text: I18n.t("job_name_label")
                    color: Theme.textPrimary
                    font.pixelSize: 12
                    font.bold: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 40
                    radius: Theme.radiusMd
                    color: Theme.surfaceElevated
                    border.color: jobNameInput.activeFocus ? Theme.primary : Theme.border
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 10
                        spacing: 8

                        TextInput {
                            id: jobNameInput
                            Layout.fillWidth: true
                            verticalAlignment: TextInput.AlignVCenter
                            color: Theme.textPrimary
                            font.pixelSize: 13
                            selectByMouse: true
                            clip: true

                            Text {
                                anchors.fill: parent
                                verticalAlignment: Text.AlignVCenter
                                text: I18n.t("job_name_placeholder")
                                color: Theme.textMuted
                                font.pixelSize: 13
                                visible: !jobNameInput.text
                            }

                            onAccepted: root.submit()
                        }

                        // Clear button
                        Rectangle {
                            width: 20
                            height: 20
                            radius: 10
                            color: clearMouse.containsMouse ? Qt.rgba(255, 255, 255, 0.1) : "transparent"
                            visible: jobNameInput.text.length > 0

                            FaIcon {
                                anchors.centerIn: parent
                                icon: Icons.times
                                size: 10
                                iconColor: Theme.textMuted
                            }

                            MouseArea {
                                id: clearMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: jobNameInput.text = ""
                            }
                        }
                    }
                }

                // Error text
                Text {
                    text: root.errorMessage
                    color: Theme.error
                    font.pixelSize: 11
                    visible: root.errorMessage.length > 0
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                }
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

                // Submit Button
                Rectangle {
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 36
                    radius: Theme.radiusMd
                    color: submitMouse.containsMouse ? Theme.primaryHover : Theme.primary
                    opacity: root.isSubmitting ? 0.6 : 1.0

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6

                        FaIcon {
                            icon: Icons.check
                            size: 11
                            iconColor: "white"
                        }

                        Text {
                            text: I18n.t("create_job_submit")
                            color: "white"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }

                    MouseArea {
                        id: submitMouse
                        anchors.fill: parent
                        enabled: !root.isSubmitting
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.submit()
                    }
                }
            }
        }
    }
}
