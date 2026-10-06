import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "../components"

Flickable {
    id: root
    contentWidth: width
    contentHeight: contentCol.implicitHeight + 40
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    ScrollBar.vertical: ScrollBar {
        policy: ScrollBar.AsNeeded
    }

    property string clientStatusText: ""

    Connections {
        target: Bridge
        function onClientStatusResult(success, statusCode, msg, licenseKey) {
            root.clientStatusText = I18n.tMsg(statusCode) + " — " + I18n.tMsg(msg);
            if (licenseKey.length > 0 && licKeyInput.text.length === 0) {
                licKeyInput.text = licenseKey;
            }
        }
        function onClientProfileResult(success, msg) {
            root.clientStatusText = I18n.tMsg(msg);
        }
    }

    ColumnLayout {
        id: contentCol
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 24
        spacing: 24

        // ---------------------------------------------------------
        // Header Section
        // ---------------------------------------------------------
        ColumnLayout {
            spacing: 4
            Text {
                text: I18n.t("settings_title")
                color: Theme.textPrimary
                font.pixelSize: 20
                font.bold: true
            }
            Text {
                text: I18n.t("settings_subtitle")
                color: Theme.textMuted
                font.pixelSize: 12
            }
        }

        // ---------------------------------------------------------
        // Card 1: Interface Language (EN / FR only)
        // ---------------------------------------------------------
        Rectangle {
            Layout.fillWidth: true
            radius: Theme.radiusMd
            color: Theme.surface
            border.color: Theme.border
            border.width: 1
            implicitHeight: langCol.implicitHeight + 32

            ColumnLayout {
                id: langCol
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                RowLayout {
                    spacing: 10
                    FaIcon {
                        icon: Icons.globe
                        size: 15
                        iconColor: Theme.primaryLight
                    }
                    ColumnLayout {
                        spacing: 2
                        Text {
                            text: I18n.t("section_language_title")
                            color: Theme.textPrimary
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Text {
                            text: I18n.t("section_language_desc")
                            color: Theme.textMuted
                            font.pixelSize: 11
                        }
                    }
                }

                RowLayout {
                    spacing: 12
                    Layout.topMargin: 4

                    // English Button
                    Rectangle {
                        width: 160
                        height: 42
                        radius: Theme.radiusMd
                        color: I18n.currentLanguage === "en" ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Theme.surfaceElevated
                        border.color: I18n.currentLanguage === "en" ? Theme.primary : Theme.border
                        border.width: 1

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            FaIcon {
                                icon: Icons.check
                                size: 12
                                iconColor: Theme.primaryLight
                                visible: I18n.currentLanguage === "en"
                            }
                            Text {
                                text: "English (EN)"
                                color: I18n.currentLanguage === "en" ? "white" : Theme.textSecondary
                                font.pixelSize: 12
                                font.bold: I18n.currentLanguage === "en"
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: I18n.setLanguage("en")
                        }
                    }

                    // Français Button
                    Rectangle {
                        width: 160
                        height: 42
                        radius: Theme.radiusMd
                        color: I18n.currentLanguage === "fr" ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Theme.surfaceElevated
                        border.color: I18n.currentLanguage === "fr" ? Theme.primary : Theme.border
                        border.width: 1

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            FaIcon {
                                icon: Icons.check
                                size: 12
                                iconColor: Theme.primaryLight
                                visible: I18n.currentLanguage === "fr"
                            }
                            Text {
                                text: "Français (FR)"
                                color: I18n.currentLanguage === "fr" ? "white" : Theme.textSecondary
                                font.pixelSize: 12
                                font.bold: I18n.currentLanguage === "fr"
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: I18n.setLanguage("fr")
                        }
                    }
                }
            }
        }

        // ---------------------------------------------------------
        // Card 2: 30-Day Free Trial (Net Time Verified)
        // ---------------------------------------------------------
        Rectangle {
            Layout.fillWidth: true
            radius: Theme.radiusMd
            color: Theme.surface
            border.color: Theme.border
            border.width: 1
            implicitHeight: trialCol.implicitHeight + 32

            ColumnLayout {
                id: trialCol
                anchors.fill: parent
                anchors.margins: 16
                spacing: 14

                RowLayout {
                    spacing: 10
                    FaIcon {
                        icon: Icons.clock
                        size: 15
                        iconColor: Theme.primaryLight
                    }
                    ColumnLayout {
                        spacing: 2
                        Text {
                            text: I18n.t("section_trial_title")
                            color: Theme.textPrimary
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Text {
                            text: I18n.t("section_trial_desc")
                            color: Theme.textMuted
                            font.pixelSize: 11
                        }
                    }

                    Item { Layout.fillWidth: true }

                    // Refresh Network Time Button
                    Rectangle {
                        height: 32
                        width: 170
                        radius: Theme.radiusMd
                        color: refreshMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Theme.surfaceElevated
                        border.color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.4)

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 6
                            FaIcon {
                                icon: Icons.sync
                                size: 11
                                iconColor: Theme.primaryLight
                            }
                            Text {
                                text: I18n.t("trial_refresh_btn")
                                color: Theme.primaryLight
                                font.pixelSize: 11
                                font.bold: true
                            }
                        }

                        MouseArea {
                            id: refreshMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Bridge.refreshTrialStatus()
                        }
                    }
                }

                // Countdown Pill & Details Display
                RowLayout {
                    spacing: 16
                    Layout.fillWidth: true

                    // Big Countdown Box
                    Rectangle {
                        width: 260
                        height: 70
                        radius: Theme.radiusMd
                        color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15)
                        border.color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.4)

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 2
                            RowLayout {
                                spacing: 8
                                Text {
                                    text: Bridge.trialDaysRemaining + " " + I18n.t("days_left") + ", " + Bridge.trialHoursRemaining + "h"
                                    color: Theme.primaryLight
                                    font.pixelSize: 17
                                    font.bold: true
                                }
                            }
                            Text {
                                text: I18n.t("trial_remaining_suffix")
                                color: Theme.textMuted
                                font.pixelSize: 10
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                    }

                    // Metadata details column
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        RowLayout {
                            spacing: 6
                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                color: Bridge.isNetworkTimeSynced ? Theme.success : Theme.warning
                            }
                            Text {
                                text: Bridge.isNetworkTimeSynced ? I18n.t("trial_net_verified") : I18n.t("trial_local_verified")
                                color: Bridge.isNetworkTimeSynced ? Theme.success : Theme.warning
                                font.pixelSize: 11
                                font.bold: true
                            }
                        }

                        Text {
                            text: I18n.t("trial_expires_on") + Bridge.trialExpiresAt
                            color: Theme.textSecondary
                            font.pixelSize: 11
                        }
                    }
                }
            }
        }

        // ---------------------------------------------------------
        // Card 3: Workstation License & Customer Details
        // ---------------------------------------------------------
        GridLayout {
        Layout.fillWidth: true
        columns: contentCol.width >= 720 ? 2 : 1
        columnSpacing: 16
        rowSpacing: 16

        // Left: Workstation License & Customer Details
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.minimumWidth: 0
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignTop
            clip: true
            radius: Theme.radiusMd
            color: Theme.surface
            border.color: Theme.border
            border.width: 1
            implicitHeight: licenseCol.implicitHeight + 32

            ColumnLayout {
                id: licenseCol
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 16
                spacing: 16

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    FaIcon {
                        icon: Icons.shield
                        size: 15
                        iconColor: Theme.primaryLight
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: I18n.t("section_license_title")
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            color: Theme.textPrimary
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Text {
                            text: I18n.t("section_license_desc")
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            color: Theme.textMuted
                            font.pixelSize: 11
                        }
                    }
                }

                // Grid of Details
                GridLayout {
                    columns: 2
                    columnSpacing: 20
                    rowSpacing: 12
                    Layout.fillWidth: true

                    // Hardware Device ID
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.columnSpan: 2
                        spacing: 4
                        Text {
                            text: I18n.t("field_device_id")
                            color: Theme.textMuted
                            font.pixelSize: 10
                            font.bold: true
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Rectangle {
                                Layout.fillWidth: true
                                height: 34
                                radius: 6
                                color: Theme.surfaceElevated
                                border.color: Theme.border
                                Text {
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 10
                                    verticalAlignment: Text.AlignVCenter
                                    text: Bridge.deviceId
                                    color: Theme.textPrimary
                                    font.pixelSize: 11
                                    font.family: "Monospace"
                                    elide: Text.ElideMiddle
                                }
                            }
                            Rectangle {
                                width: 70
                                height: 34
                                radius: 6
                                color: copyDevMouse.containsMouse ? Theme.primaryHover : Theme.primary
                                Text {
                                    anchors.centerIn: parent
                                    text: I18n.t("btn_copy")
                                    color: "white"
                                    font.pixelSize: 11
                                    font.bold: true
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

                    // License Status
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: I18n.t("field_license_status")
                            color: Theme.textMuted
                            font.pixelSize: 10
                            font.bold: true
                        }
                        Rectangle {
                            height: 32
                            width: 140
                            radius: 6
                            color: {
                                if (Bridge.licenseStatusCode === "ACTIVE") return Qt.rgba(Theme.success.r, Theme.success.g, Theme.success.b, 0.2);
                                if (Bridge.licenseStatusCode === "TRIAL") return Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2);
                                return Qt.rgba(Theme.error.r, Theme.error.g, Theme.error.b, 0.2);
                            }
                            border.color: {
                                if (Bridge.licenseStatusCode === "ACTIVE") return Theme.success;
                                if (Bridge.licenseStatusCode === "TRIAL") return Theme.primaryLight;
                                return Theme.error;
                            }
                            Text {
                                anchors.centerIn: parent
                                text: {
                                    if (Bridge.licenseStatusCode === "ACTIVE") return I18n.t("status_licensed");
                                    if (Bridge.licenseStatusCode === "TRIAL") return I18n.t("status_trial");
                                    return I18n.t("status_activation_required");
                                }
                                color: {
                                    if (Bridge.licenseStatusCode === "ACTIVE") return Theme.success;
                                    if (Bridge.licenseStatusCode === "TRIAL") return Theme.primaryLight;
                                    return Theme.error;
                                }
                                font.pixelSize: 11
                                font.bold: true
                            }
                        }
                    }

                    // License Expiration
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: I18n.t("field_expires_at")
                            color: Theme.textMuted
                            font.pixelSize: 10
                            font.bold: true
                        }
                        Text {
                            text: Bridge.licenseExpiresAt || "Perpetual"
                            color: Theme.textPrimary
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }

                    // Customer Name
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: I18n.t("field_customer_name")
                            color: Theme.textMuted
                            font.pixelSize: 10
                            font.bold: true
                        }
                        Text {
                            text: Bridge.customerName || "—"
                            color: Theme.textPrimary
                            font.pixelSize: 12
                        }
                    }

                    // Customer Email
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: I18n.t("field_customer_email")
                            color: Theme.textMuted
                            font.pixelSize: 10
                            font.bold: true
                        }
                        Text {
                            text: Bridge.customerEmail || "—"
                            color: Theme.textPrimary
                            font.pixelSize: 12
                        }
                    }

                    // Customer Phone
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: I18n.t("field_customer_phone")
                            color: Theme.textMuted
                            font.pixelSize: 10
                            font.bold: true
                        }
                        Text {
                            text: Bridge.customerPhone || "—"
                            color: Theme.textPrimary
                            font.pixelSize: 12
                        }
                    }

                    // Active License Key
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: I18n.t("field_license_key")
                            color: Theme.textMuted
                            font.pixelSize: 10
                            font.bold: true
                        }
                        Text {
                            text: Bridge.licenseKey ? (Bridge.licenseKey.slice(0, 10) + "••••••••••••") : "—"
                            color: Theme.textPrimary
                            font.pixelSize: 12
                            font.family: "Monospace"
                        }
                    }
                }

            }
        }

        // Right: Activate or Change License
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.minimumWidth: 0
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignTop
            clip: true
            radius: Theme.radiusMd
            color: Theme.surface
            border.color: Theme.border
            border.width: 1
            implicitHeight: activateCol.implicitHeight + 32

                ColumnLayout {
                    id: activateCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 16
                    spacing: 10

                    Text {
                        text: I18n.t("activate_section_title")
                        color: Theme.textPrimary
                        font.pixelSize: 13
                        font.bold: true
                    }
                    Text {
                        text: I18n.t("activate_section_desc")
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                        color: Theme.textMuted
                        font.pixelSize: 11
                    }

                    Text {
                        text: I18n.t("section_details_title")
                        color: Theme.textSecondary
                        font.pixelSize: 11
                        font.bold: true
                        Layout.topMargin: 6
                    }
                    Text {
                        text: I18n.t("section_details_desc")
                        color: Theme.textMuted
                        font.pixelSize: 10
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    GridLayout {
                        columns: 2
                        columnSpacing: 14
                        rowSpacing: 10
                        Layout.fillWidth: true

                        // Full Name Input
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: I18n.t("customer_name_label")
                                color: Theme.textSecondary
                                font.pixelSize: 11
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 36
                                radius: 6
                                color: Theme.surfaceElevated
                                border.color: nameInput.activeFocus ? Theme.primary : Theme.border
                                TextInput {
                                    id: nameInput
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 10
                                    verticalAlignment: Text.AlignVCenter
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    selectByMouse: true
                                    Text {
                                        text: I18n.t("customer_name_placeholder")
                                        color: Theme.textMuted
                                        font.pixelSize: 12
                                        visible: !nameInput.text && !nameInput.activeFocus
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }

                        // Email Input
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: I18n.t("email_label")
                                color: Theme.textSecondary
                                font.pixelSize: 11
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 36
                                radius: 6
                                color: Theme.surfaceElevated
                                border.color: emailInput.activeFocus ? Theme.primary : Theme.border
                                TextInput {
                                    id: emailInput
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 10
                                    verticalAlignment: Text.AlignVCenter
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    selectByMouse: true
                                    Text {
                                        text: I18n.t("email_placeholder")
                                        color: Theme.textMuted
                                        font.pixelSize: 12
                                        visible: !emailInput.text && !emailInput.activeFocus
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }

                        // Phone Input
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: I18n.t("phone_label")
                                color: Theme.textSecondary
                                font.pixelSize: 11
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 36
                                radius: 6
                                color: Theme.surfaceElevated
                                border.color: phoneInput.activeFocus ? Theme.primary : Theme.border
                                TextInput {
                                    id: phoneInput
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 10
                                    verticalAlignment: Text.AlignVCenter
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    selectByMouse: true
                                    Text {
                                        text: I18n.t("phone_placeholder")
                                        color: Theme.textMuted
                                        font.pixelSize: 12
                                        visible: !phoneInput.text && !phoneInput.activeFocus
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }

                        // Address Input
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: I18n.t("address_label")
                                color: Theme.textSecondary
                                font.pixelSize: 11
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 36
                                radius: 6
                                color: Theme.surfaceElevated
                                border.color: addrInput.activeFocus ? Theme.primary : Theme.border
                                TextInput {
                                    id: addrInput
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 10
                                    verticalAlignment: Text.AlignVCenter
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    selectByMouse: true
                                    Text {
                                        text: I18n.t("address_placeholder")
                                        color: Theme.textMuted
                                        font.pixelSize: 12
                                        visible: !addrInput.text && !addrInput.activeFocus
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                    }

                    // Request Key / Check Status
                    RowLayout {
                        Layout.topMargin: 6
                        spacing: 8

                        Rectangle {
                            width: registerBtnRow.implicitWidth + 28
                            height: 40
                            radius: 8
                            color: registerMouse.containsMouse ? Theme.primaryHover : Theme.primary

                            RowLayout {
                                id: registerBtnRow
                                anchors.centerIn: parent
                                spacing: 8
                                FaIcon {
                                    icon: Icons.plus
                                    size: 12
                                    iconColor: "white"
                                }
                                Text {
                                    text: I18n.t("register_btn")
                                    color: "white"
                                    font.pixelSize: 12
                                    font.bold: true
                                }
                            }

                            MouseArea {
                                id: registerMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    var name = nameInput.text.trim();
                                    var email = emailInput.text.trim();
                                    var phone = phoneInput.text.trim();
                                    var addr = addrInput.text.trim();

                                    if (name.length < 2) {
                                        Bridge.toast("error", I18n.t("val_name_err"));
                                        return;
                                    }
                                    if (email.length < 5 || email.indexOf("@") === -1) {
                                        Bridge.toast("error", I18n.t("val_email_err"));
                                        return;
                                    }
                                    if (phone.length < 6 || phone.indexOf("+213") !== 0) {
                                        Bridge.toast("error", I18n.t("val_phone_err"));
                                        return;
                                    }

                                    root.clientStatusText = "";
                                    Bridge.registerClientProfile(name, email, phone, addr);
                                }
                            }
                        }

                        Rectangle {
                            width: statusBtnRow.implicitWidth + 28
                            height: 40
                            radius: 8
                            color: statusMouse.containsMouse ? Theme.surfaceElevated : Theme.surface
                            border.color: Theme.border

                            RowLayout {
                                id: statusBtnRow
                                anchors.centerIn: parent
                                spacing: 8
                                FaIcon {
                                    icon: Icons.sync
                                    size: 12
                                    iconColor: Theme.textMuted
                                }
                                Text {
                                    text: I18n.t("check_status_btn")
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    font.bold: true
                                }
                            }

                            MouseArea {
                                id: statusMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    var query = emailInput.text.trim() || phoneInput.text.trim() || Bridge.deviceId;
                                    root.clientStatusText = "";
                                    Bridge.checkClientStatus(query);
                                }
                            }
                        }
                    }

                    // -------------------------------------------------
                    // Already have a key: key input + Activate button
                    // -------------------------------------------------
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: haveKeyCol.implicitHeight + 28
                        radius: 8
                        color: Theme.surfaceElevated
                        border.color: Theme.border

                        ColumnLayout {
                            id: haveKeyCol
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 14
                            spacing: 8

                            Text {
                                text: I18n.t("section_have_key_title")
                                color: Theme.textPrimary
                                font.pixelSize: 12
                                font.bold: true
                            }
                            Text {
                                text: I18n.t("section_have_key_desc")
                                color: Theme.textMuted
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }

                            // License Key Input
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                Text {
                                    text: I18n.t("license_key_label")
                                    color: Theme.textSecondary
                                    font.pixelSize: 11
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 36
                                    radius: 6
                                    color: Theme.surface
                                    border.color: licKeyInput.activeFocus ? Theme.primary : Theme.border
                                    TextInput {
                                        id: licKeyInput
                                        anchors.fill: parent
                                        anchors.leftMargin: 10
                                        anchors.rightMargin: 10
                                        verticalAlignment: Text.AlignVCenter
                                        color: Theme.textPrimary
                                        font.pixelSize: 12
                                        font.family: "Monospace"
                                        selectByMouse: true
                                        Text {
                                            text: I18n.t("license_key_placeholder")
                                            color: Theme.textMuted
                                            font.pixelSize: 12
                                            font.family: "Monospace"
                                            visible: !licKeyInput.text && !licKeyInput.activeFocus
                                            anchors.fill: parent
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                    }
                                }
                            }

                            // Activate Workstation
                            RowLayout {
                                Layout.topMargin: 6
                                spacing: 8

                                Rectangle {
                                    width: 180
                                    height: 40
                                    radius: 8
                                    color: activateMouse.containsMouse ? Theme.primaryHover : Theme.primary

                                    RowLayout {
                                        anchors.centerIn: parent
                                        spacing: 8
                                        FaIcon {
                                            icon: Icons.key
                                            size: 12
                                            iconColor: "white"
                                        }
                                        Text {
                                            text: I18n.t("activate_btn")
                                            color: "white"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                    }

                                    MouseArea {
                                        id: activateMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            var key = licKeyInput.text.trim();
                                            var name = nameInput.text.trim();
                                            var email = emailInput.text.trim();
                                            var phone = phoneInput.text.trim();
                                            var addr = addrInput.text.trim();

                                            if (key.length < 10) {
                                                Bridge.toast("error", I18n.t("val_key_err"));
                                                return;
                                            }
                                            // Customer details are optional (openapi.json); when any is
                                            // provided, CustomerDetailsSchema requires all three.
                                            if (name.length > 0 || email.length > 0 || phone.length > 0) {
                                                if (name.length < 2) {
                                                    Bridge.toast("error", I18n.t("val_name_err"));
                                                    return;
                                                }
                                                if (email.length < 5 || email.indexOf("@") === -1) {
                                                    Bridge.toast("error", I18n.t("val_email_err"));
                                                    return;
                                                }
                                                if (phone.length < 6 || phone.indexOf("+213") !== 0) {
                                                    Bridge.toast("error", I18n.t("val_phone_err"));
                                                    return;
                                                }
                                            }

                                            Bridge.activateLicense(key, name, email, phone, addr);
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Text {
                        visible: root.clientStatusText.length > 0
                        text: root.clientStatusText
                        color: Theme.textMuted
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }
        }

        // ---------------------------------------------------------
        // Card 5: Application Details (Bilnov, contact numbers, Correct Version)
        // ---------------------------------------------------------
        Rectangle {
            Layout.fillWidth: true
            radius: Theme.radiusMd
            color: Theme.surface
            border.color: Theme.border
            border.width: 1
            implicitHeight: appInfoCol.implicitHeight + 28

            ColumnLayout {
                id: appInfoCol
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                Text {
                    text: I18n.t("section_app_info_title")
                    color: Theme.textPrimary
                    font.pixelSize: 13
                    font.bold: true
                }

                RowLayout {
                    spacing: 36
                    Layout.fillWidth: true

                    // Application Name
                    ColumnLayout {
                        spacing: 2
                        Text {
                            text: I18n.t("app_name_label")
                            color: Theme.textMuted
                            font.pixelSize: 10
                        }
                        Text {
                            text: "Bilnov Gallery Desktop"
                            color: Theme.textPrimary
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }

                    // Version
                    ColumnLayout {
                        spacing: 2
                        Text {
                            text: I18n.t("app_version_label")
                            color: Theme.textMuted
                            font.pixelSize: 10
                        }
                        Text {
                            text: Bridge.appVersion || "v1.4.0"
                            color: Theme.primaryLight
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }

                    // Developed by
                    ColumnLayout {
                        spacing: 2
                        Text {
                            text: I18n.t("app_developer_label")
                            color: Theme.textMuted
                            font.pixelSize: 10
                        }
                        RowLayout {
                            spacing: 6
                            Rectangle {
                                width: 18
                                height: 18
                                radius: 4
                                color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2)
                                Text {
                                    anchors.centerIn: parent
                                    text: "B"
                                    color: Theme.primaryLight
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }
                            Text {
                                text: "Bilnov"
                                color: Theme.textPrimary
                                font.pixelSize: 12
                                font.bold: true
                            }
                        }
                    }

                    // Contact Phone Numbers
                    ColumnLayout {
                        spacing: 4
                        Text {
                            text: I18n.t("app_phone_label")
                            color: Theme.textMuted
                            font.pixelSize: 10
                        }
                        Repeater {
                            model: ["+213775189229", "+213796629314"]
                            RowLayout {
                                spacing: 8
                                Text {
                                    text: modelData
                                    color: Theme.primaryLight
                                    font.pixelSize: 12
                                    font.family: "Monospace"
                                    font.bold: true
                                }
                                Rectangle {
                                    width: 22
                                    height: 22
                                    radius: 4
                                    color: copyPhoneMouse.containsMouse ? Theme.primaryHover : Theme.surfaceElevated
                                    border.color: Theme.border
                                    FaIcon {
                                        anchors.centerIn: parent
                                        icon: Icons.copy
                                        size: 10
                                        iconColor: copyPhoneMouse.containsMouse ? "white" : Theme.textMuted
                                    }
                                    MouseArea {
                                        id: copyPhoneMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            Bridge.copyToClipboard(modelData)
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
