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
    z: 99999
    visible: opacity > 0
    opacity: 0

    property bool isMandatory: !Bridge.isLicensed
    property bool isSubmitting: false
    property string errorMessage: ""
    property string infoText: ""
    // 1 = submit details & receive key via WhatsApp/phone, 2 = enter received key
    property int step: 1

    Behavior on opacity { NumberAnimation { duration: 200; easing.type: Easing.OutQuad } }

    function open() {
        root.errorMessage = ""
        root.infoText = ""
        root.isSubmitting = false
        root.step = (Bridge.licenseKey && Bridge.licenseKey.length >= 10) ? 2 : 1
        root.opacity = 1
        if (root.step === 2) {
            keyInput.forceActiveFocus()
        } else {
            nameInput.forceActiveFocus()
        }
    }

    function close() {
        if (!root.isMandatory || Bridge.isLicensed) {
            root.opacity = 0
        }
    }

    function goStep(n) {
        root.step = n
        root.errorMessage = ""
        root.infoText = ""
        if (n === 2) {
            keyInput.forceActiveFocus()
        } else {
            nameInput.forceActiveFocus()
        }
    }

    Connections {
        target: Bridge
        function onActivationResult(success, msg) {
            root.isSubmitting = false
            if (success) {
                root.errorMessage = ""
                root.close()
            } else {
                root.errorMessage = I18n.tMsg(msg)
            }
        }
        function onClientProfileResult(success, msg) {
            root.isSubmitting = false
            if (success) {
                root.errorMessage = ""
                root.infoText = I18n.tMsg(msg) + " " + I18n.t("whatsapp_delivery_note")
            } else {
                root.infoText = ""
                root.errorMessage = I18n.tMsg(msg)
            }
        }
        function onClientStatusResult(success, statusCode, msg, licenseKey) {
            root.isSubmitting = false
            root.errorMessage = success ? "" : I18n.tMsg(msg)
            root.infoText = success ? (I18n.tMsg(statusCode) + " — " + I18n.tMsg(msg)) : ""
            if (success && licenseKey.length > 0) {
                keyInput.text = licenseKey
                root.step = 2
            }
        }
    }

    // Dismiss on clicking backdrop (only if not mandatory)
    MouseArea {
        anchors.fill: parent
        onClicked: {
            if (!root.isMandatory) root.close()
        }
    }

    // Center Modal Box
    Rectangle {
        id: dialogBox
        width: 520
        height: Math.min(680, parent.height - 40)
        anchors.centerIn: parent
        radius: Theme.radiusLg
        color: "#0F172A"
        border.color: "#334155"
        border.width: 1
        clip: true

        // Stop clicks from reaching backdrop
        MouseArea {
            anchors.fill: parent
            propagateComposedEvents: false
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 28
            spacing: 16

            // Header Row
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Rectangle {
                    width: 44
                    height: 44
                    radius: 10
                    color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2)
                    border.color: Qt.rgba(Theme.primaryLight.r, Theme.primaryLight.g, Theme.primaryLight.b, 0.4)

                    FaIcon {
                        anchors.centerIn: parent
                        icon: Icons.shield
                        size: 20
                        iconColor: Theme.primaryLight
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: I18n.t("activation_title")
                        color: "#F8FAFC"
                        font.pixelSize: 18
                        font.bold: true
                        horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                    }

                    Text {
                        text: I18n.t("activation_subtitle")
                        color: "#94A3B8"
                        font.pixelSize: 11
                        horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                    }
                }

                // Close Button (visible only when already licensed)
                Rectangle {
                    visible: !root.isMandatory || Bridge.isLicensed
                    width: 32
                    height: 32
                    radius: 6
                    color: closeMouse.containsMouse ? "#1E293B" : "transparent"

                    FaIcon {
                        anchors.centerIn: parent
                        icon: Icons.times
                        size: 14
                        iconColor: "#94A3B8"
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

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#1E293B"
            }

            // Step Segmented Control
            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    radius: 8
                    color: root.step === 1 ? Theme.primary : "#111827"
                    border.color: root.step === 1 ? Theme.primaryLight : "#334155"

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6
                        layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight
                        FaIcon {
                            icon: Icons.plus
                            size: 11
                            iconColor: root.step === 1 ? "white" : "#94A3B8"
                        }
                        Text {
                            text: I18n.t("seg_step1")
                            color: root.step === 1 ? "white" : "#94A3B8"
                            font.pixelSize: 12
                            font.bold: root.step === 1
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.goStep(1)
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    radius: 8
                    color: root.step === 2 ? Theme.primary : "#111827"
                    border.color: root.step === 2 ? Theme.primaryLight : "#334155"

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6
                        layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight
                        FaIcon {
                            icon: Icons.key
                            size: 11
                            iconColor: root.step === 2 ? "white" : "#94A3B8"
                        }
                        Text {
                            text: I18n.t("seg_step2")
                            color: root.step === 2 ? "white" : "#94A3B8"
                            font.pixelSize: 12
                            font.bold: root.step === 2
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.goStep(2)
                    }
                }
            }

            // Scrollable Form Content
            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: formCol.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                ColumnLayout {
                    id: formCol
                    width: parent.width
                    spacing: 12

                    // Step Header
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: root.step === 1 ? I18n.t("step1_title") : I18n.t("step2_title")
                            color: "#F8FAFC"
                            font.pixelSize: 13
                            font.bold: true
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                            horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                        }
                        Text {
                            text: root.step === 1 ? I18n.t("step1_desc") : I18n.t("step2_desc")
                            color: "#94A3B8"
                            font.pixelSize: 11
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                            horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                        }
                    }

                    // Device Hardware ID Badge
                    Rectangle {
                        Layout.fillWidth: true
                        height: 52
                        radius: 8
                        color: "#090D16"
                        border.color: "#1E293B"

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Text {
                                    text: I18n.t("device_fingerprint")
                                    color: "#64748B"
                                    font.pixelSize: 9
                                    font.bold: true
                                }
                                Text {
                                    text: Bridge.deviceId
                                    color: "#38BDF8"
                                    font.pixelSize: 10
                                    font.family: Qt.platform.os === "osx" ? "Menlo" : "monospace"
                                    elide: Text.ElideMiddle
                                    Layout.fillWidth: true
                                }
                            }

                            Rectangle {
                                width: 28
                                height: 28
                                radius: 4
                                color: copyDevMouse.containsMouse ? "#1E293B" : "transparent"

                                FaIcon {
                                    anchors.centerIn: parent
                                    icon: Icons.copy
                                    size: 12
                                    iconColor: "#94A3B8"
                                }

                                MouseArea {
                                    id: copyDevMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: Bridge.copyToClipboard(Bridge.deviceId)
                                }
                            }
                        }
                    }

                    // -----------------------------------------------------
                    // Step 1: Customer details submitted to /client/profile
                    // -----------------------------------------------------
                    ColumnLayout {
                        visible: root.step === 1
                        Layout.fillWidth: true
                        spacing: 12

                        // Full Legal Name
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: I18n.t("customer_name_label")
                                color: "#E2E8F0"
                                font.pixelSize: 11
                                font.bold: true
                                horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 38
                                radius: 6
                                color: "#1E293B"
                                border.color: nameInput.activeFocus ? Theme.primary : "#334155"

                                TextInput {
                                    id: nameInput
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    text: Bridge.customerName
                                    color: "#F8FAFC"
                                    font.pixelSize: 12
                                    selectByMouse: true
                                    clip: true
                                    horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft

                                    Text {
                                        text: I18n.t("customer_name_placeholder")
                                        color: "#64748B"
                                        font.pixelSize: 12
                                        visible: !nameInput.text && !nameInput.activeFocus
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
                                        horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                                    }
                                }
                            }
                        }

                        // Contact Email
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: I18n.t("email_label")
                                color: "#E2E8F0"
                                font.pixelSize: 11
                                font.bold: true
                                horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 38
                                radius: 6
                                color: "#1E293B"
                                border.color: emailInput.activeFocus ? Theme.primary : "#334155"

                                TextInput {
                                    id: emailInput
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    color: "#F8FAFC"
                                    font.pixelSize: 12
                                    selectByMouse: true
                                    clip: true
                                    horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft

                                    Text {
                                        text: I18n.t("email_placeholder")
                                        color: "#64748B"
                                        font.pixelSize: 12
                                        visible: !emailInput.text && !emailInput.activeFocus
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
                                        horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                                    }
                                }
                            }
                        }

                        // Phone Number (WhatsApp delivery target)
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: I18n.t("phone_label")
                                color: "#E2E8F0"
                                font.pixelSize: 11
                                font.bold: true
                                horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 38
                                radius: 6
                                color: "#1E293B"
                                border.color: phoneInput.activeFocus ? Theme.primary : "#334155"

                                TextInput {
                                    id: phoneInput
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    color: "#F8FAFC"
                                    font.pixelSize: 12
                                    selectByMouse: true
                                    clip: true
                                    horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft

                                    Text {
                                        text: I18n.t("phone_placeholder")
                                        color: "#64748B"
                                        font.pixelSize: 12
                                        visible: !phoneInput.text && !phoneInput.activeFocus
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
                                        horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                                    }
                                }
                            }
                        }

                        // Physical Address (Optional)
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: I18n.t("address_label")
                                color: "#E2E8F0"
                                font.pixelSize: 11
                                horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 38
                                radius: 6
                                color: "#1E293B"
                                border.color: addrInput.activeFocus ? Theme.primary : "#334155"

                                TextInput {
                                    id: addrInput
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    color: "#F8FAFC"
                                    font.pixelSize: 12
                                    selectByMouse: true
                                    clip: true
                                    horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft

                                    Text {
                                        text: I18n.t("address_placeholder")
                                        color: "#64748B"
                                        font.pixelSize: 12
                                        visible: !addrInput.text && !addrInput.activeFocus
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
                                        horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                                    }
                                }
                            }
                        }
                    }

                    // -----------------------------------------------------
                    // Step 2: Enter the key received by WhatsApp / phone
                    // -----------------------------------------------------
                    ColumnLayout {
                        visible: root.step === 2
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: I18n.t("license_key_label")
                            color: "#E2E8F0"
                            font.pixelSize: 11
                            font.bold: true
                            horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            height: 38
                            radius: 6
                            color: "#1E293B"
                            border.color: keyInput.activeFocus ? Theme.primary : "#334155"

                            TextInput {
                                id: keyInput
                                anchors.fill: parent
                                anchors.margins: 10
                                text: Bridge.licenseKey
                                color: "#F8FAFC"
                                font.pixelSize: 12
                                selectByMouse: true
                                clip: true
                                horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft

                                Text {
                                    text: "ZED-XXXX-XXXX-XXXX"
                                    color: "#64748B"
                                    font.pixelSize: 12
                                    visible: !keyInput.text && !keyInput.activeFocus
                                    anchors.fill: parent
                                    verticalAlignment: Text.AlignVCenter
                                    horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
                                }
                            }
                        }
                    }
                }
            }

            // Info display (registration / status results)
            Text {
                visible: !!root.infoText
                text: root.infoText
                color: "#38BDF8"
                font.pixelSize: 11
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
            }

            // Error display
            Text {
                visible: !!root.errorMessage
                text: root.errorMessage
                color: "#EF4444"
                font.pixelSize: 11
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                horizontalAlignment: I18n.isRTL ? Text.AlignRight : Text.AlignLeft
            }

            // Primary Action Button
            Rectangle {
                Layout.fillWidth: true
                height: 44
                radius: 8
                color: submitMouse.containsMouse ? Theme.primaryHover : Theme.primary
                opacity: root.isSubmitting ? 0.7 : 1.0

                RowLayout {
                    anchors.centerIn: parent
                    spacing: 8
                    layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight

                    BusyIndicator {
                        running: root.isSubmitting
                        visible: root.isSubmitting
                        width: 20
                        height: 20
                    }

                    FaIcon {
                        visible: !root.isSubmitting
                        icon: root.step === 1 ? Icons.plus : Icons.key
                        size: 13
                        iconColor: "white"
                    }

                    Text {
                        text: {
                            if (root.isSubmitting) {
                                return root.step === 1 ? I18n.t("btn_requesting") : I18n.t("btn_activating")
                            }
                            return root.step === 1 ? I18n.t("submit_details_btn") : I18n.t("btn_activate")
                        }
                        color: "white"
                        font.pixelSize: 13
                        font.bold: true
                    }
                }

                MouseArea {
                    id: submitMouse
                    anchors.fill: parent
                    enabled: !root.isSubmitting
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (root.step === 1) {
                            // Step 1: submit details to POST /api/v1/client/profile
                            var n = nameInput.text.trim();
                            var e = emailInput.text.trim();
                            var p = phoneInput.text.trim();
                            var a = addrInput.text.trim();

                            if (n.length < 2) {
                                root.errorMessage = I18n.t("val_name_err");
                                return;
                            }
                            if (e.length < 5 || e.indexOf("@") === -1) {
                                root.errorMessage = I18n.t("val_email_err");
                                return;
                            }
                            if (p.length < 6 || p.indexOf("+213") !== 0) {
                                root.errorMessage = I18n.t("val_phone_err");
                                return;
                            }

                            root.errorMessage = "";
                            root.infoText = "";
                            root.isSubmitting = true;
                            Bridge.registerClientProfile(n, e, p, a);
                        } else {
                            // Step 2: activate with the received key
                            var k = keyInput.text.trim();
                            if (k.length < 10) {
                                root.errorMessage = I18n.t("val_key_err");
                                return;
                            }

                            // Attach customer details only when the full valid set is available
                            var cn = nameInput.text.trim();
                            var ce = emailInput.text.trim();
                            var cp = phoneInput.text.trim();
                            var custOk = cn.length >= 2 && ce.length >= 5 && ce.indexOf("@") !== -1 && cp.length >= 6 && cp.indexOf("+213") === 0;

                            root.errorMessage = "";
                            root.infoText = "";
                            root.isSubmitting = true;
                            Bridge.activateLicense(k, custOk ? cn : "", custOk ? ce : "", custOk ? cp : "", custOk ? addrInput.text.trim() : "");
                        }
                    }
                }
            }

            // Secondary Row: status check + step switch
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Rectangle {
                    Layout.fillWidth: true
                    height: 38
                    radius: 8
                    color: statusMouse.containsMouse ? "#1E293B" : "#090D16"
                    border.color: "#334155"

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 8
                        layoutDirection: I18n.isRTL ? Qt.RightToLeft : Qt.LeftToRight
                        FaIcon {
                            icon: Icons.sync
                            size: 12
                            iconColor: "#94A3B8"
                        }
                        Text {
                            text: I18n.t("check_status_btn")
                            color: "#E2E8F0"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }

                    MouseArea {
                        id: statusMouse
                        anchors.fill: parent
                        enabled: !root.isSubmitting
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            var q = emailInput.text.trim() || phoneInput.text.trim() || Bridge.deviceId;
                            root.errorMessage = "";
                            root.infoText = "";
                            root.isSubmitting = true;
                            Bridge.checkClientStatus(q);
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 38
                    radius: 8
                    color: switchMouse.containsMouse ? "#1E293B" : "transparent"
                    border.color: "#334155"

                    Text {
                        anchors.centerIn: parent
                        text: root.step === 1 ? I18n.t("link_have_key") : I18n.t("link_need_key")
                        color: "#38BDF8"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    MouseArea {
                        id: switchMouse
                        anchors.fill: parent
                        enabled: !root.isSubmitting
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.goStep(root.step === 1 ? 2 : 1)
                    }
                }
            }
        }
    }
}
